from __future__ import annotations

import asyncio
import logging
import sys
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query

from backend.websocket.schemas import (
    ClientMessage,
    LandmarkFrame,
    RecognitionResult,
    ServerMessage,
    TranslationPayload,
    ComputerControlPayload,
)
from backend.websocket.manager import manager
from backend.controllers.auth import get_current_user
from fastapi import Request

router = APIRouter()
log = logging.getLogger(__name__)


def _get_app_state(websocket: WebSocket):
    return websocket.app.state


def _unpack_landmarks(lm_list):
    out = []
    for i in range(21):
        p = lm_list[i]
        if isinstance(p, dict):
            x = float(p.get("x", 0.0))
            y = float(p.get("y", 0.0))
            z = float(p.get("z", 0.0))
        elif isinstance(p, (list, tuple)):
            x = float(p[0]) if len(p) > 0 else 0.0
            y = float(p[1]) if len(p) > 1 else 0.0
            z = float(p[2]) if len(p) > 2 else 0.0
        else:
            x = float(getattr(p, "x", 0.0))
            y = float(getattr(p, "y", 0.0))
            z = float(getattr(p, "z", 0.0))

        class _Pt:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z

        out.append(_Pt(x, y, z))
    return out


@router.websocket("/ws/sign")
async def ws_sign(
    websocket: WebSocket,
):
    session_id = await manager.connect(websocket)
    state = _get_app_state(websocket)

    static_rec = getattr(state, "static_recognizer", None)
    temporal = getattr(state, "temporal_processor", None)
    dyn_rec = getattr(state, "dynamic_recognizer", None)
    translation_svc = getattr(state, "translation_service", None)
    asset_resolver = getattr(state, "asset_resolver", None)
    cc_svc = getattr(state, "computer_control", None)
    feature_fn = getattr(state, "features_to_63_fn", None)

    last_sentence_fired = ""
    last_phrase_key = ""
    current_mode: str = getattr(state, "current_mode", "COMMUNICATION")
    conf_threshold: float = 0.6

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
            except TimeoutError:
                await manager.send(
                    session_id,
                    ServerMessage(type="pong", ts=time.time()).model_dump(exclude_none=True),
                )
                continue
            except WebSocketDisconnect:
                break

            manager.touch(session_id)

            try:
                msg = ClientMessage.model_validate(data)
            except Exception as val_err:
                await manager.send(
                    session_id,
                    ServerMessage(
                        type="error",
                        message="Invalid client message: " + str(val_err),
                        ts=time.time(),
                    ).model_dump(exclude_none=True),
                )
                continue

            resp_echo = msg.echo_id

            if msg.type == "ping":
                await manager.send(
                    session_id,
                    ServerMessage(type="pong", echo_id=resp_echo, ts=time.time()).model_dump(exclude_none=True),
                )
                continue

            if msg.type == "control" and msg.control is not None:
                ctl = msg.control
                if ctl.mode is not None:
                    current_mode = ctl.mode
                    state.current_mode = current_mode
                    if cc_svc is not None:
                        cc_svc.set_active(current_mode == "CONTROL")
                if ctl.threshold is not None:
                    conf_threshold = float(ctl.threshold)
                if temporal is not None:
                    temporal.control(ctl.action)

                await manager.send(
                    session_id,
                    ServerMessage(
                        type="control_status",
                        recognition=RecognitionResult(
                            status=temporal._last_sign is not None and "confirmed" or "idle",
                            sign=temporal._last_sign,
                            confidence=temporal._last_confidence,
                            current_word=temporal.builder.current_word,
                            sentence=temporal.builder.sentence.rstrip(),
                            changed=False,
                            mode=current_mode,  # type: ignore[arg-type]
                        ),
                        echo_id=resp_echo,
                        ts=time.time(),
                    ).model_dump(exclude_none=True),
                )
                continue

            if msg.type != "frame" or msg.frame is None:
                continue

            frame: LandmarkFrame = msg.frame
            now_ts = time.time()

            try:
                pts = _unpack_landmarks(frame.hand_landmarks)
            except Exception as unpack_err:
                await manager.send(
                    session_id,
                    ServerMessage(
                        type="error",
                        message="Landmark unpack error: " + str(unpack_err),
                        ts=time.time(),
                    ).model_dump(exclude_none=True),
                )
                continue

            rec_result = {
                "status": "idle",
                "sign": None,
                "kind": None,
                "confidence": 0.0,
                "current_word": temporal.builder.current_word if temporal else "",
                "sentence": temporal.builder.sentence.rstrip() if temporal else "",
                "changed": False,
                "mode": current_mode,
            }

            cc_payload: dict[str, Any] = {
                "moved": False, "clicked": False, "scrolled_clicks": 0, "launched_app": None,
            }

            if cc_svc is not None and current_mode == "CONTROL":
                cc_payload = cc_svc.step(pts)

            raw_pred = None
            if static_rec is not None and current_mode != "CONTROL":
                try:
                    raw_pred = static_rec.predict(
                        pts, conf_threshold=conf_threshold, mode=current_mode.lower() if current_mode else "communication"
                    )
                except Exception as rec_err:
                    log.warning("static_rec.predict error %s", rec_err)
                    raw_pred = None

            if feature_fn is not None and dyn_rec is not None:
                feat63 = feature_fn(pts)
                dyn_rec.add_frame(feat63)
                if raw_pred is None and dyn_rec.ready():
                    dyn_out = dyn_rec.predict()
                    if dyn_out is not None:
                        raw_pred = dyn_out

            if temporal is not None:
                step_out = temporal.step(raw_pred, now_ts=now_ts)
                rec_result.update({
                    "status": step_out.get("status", "idle"),
                    "sign": step_out.get("sign"),
                    "kind": raw_pred.get("kind") if raw_pred else None,
                    "confidence": step_out.get("confidence", 0.0),
                    "current_word": step_out.get("current_word", ""),
                    "sentence": step_out.get("sentence", ""),
                    "changed": step_out.get("changed", False),
                    "mode": current_mode,
                })

            phrase_status_out = None
            translation_out = None

            if raw_pred is not None and raw_pred.get("kind") == "phrase":
                sign_key = raw_pred.get("sign")
                if sign_key is not None and asset_resolver is not None and translation_svc is not None:
                    if sign_key != last_phrase_key:
                        resolved = asset_resolver.resolve(sign_key)
                        tr = translation_svc.translate_phrase(sign_key)
                        last_phrase_key = sign_key
                        phrase_status_out = {
                            "key": sign_key,
                            "english": tr.get("en"),
                            "hindi": tr.get("hi"),
                            "telugu": tr.get("te"),
                            "spanish": tr.get("es"),
                            "french": tr.get("fr"),
                        }
                        translation_out = TranslationPayload(
                            key=resolved.get("key", sign_key),
                            display=resolved.get("display", sign_key),
                            description=resolved.get("description", ""),
                            translations=tr,
                            image=resolved.get("image", ""),
                            auto_translated=tr.get("auto_translated", False),
                        )

            if rec_result["sentence"] and rec_result["sentence"] != last_sentence_fired and rec_result.get("changed"):
                last_sentence_fired = rec_result["sentence"]
                try:
                    history_store = getattr(state, "history_store", None)
                    if history_store is not None and translation_svc is not None:
                        full_sentence = rec_result["sentence"]
                        if asset_resolver is not None:
                            tr = translation_svc.translate_sentence(full_sentence)
                            history_store.append({
                                "ts": now_ts * 1000,
                                "text": full_sentence,
                                "mode": current_mode,
                                "languages": {
                                    "en": tr.get("en"),
                                    "hi": tr.get("hi"),
                                    "te": tr.get("te"),
                                    "es": tr.get("es"),
                                    "fr": tr.get("fr"),
                                },
                            })
                except Exception as hist_err:
                    log.debug("history store error %s", hist_err)

            server_msg = ServerMessage(
                type="recognition",
                recognition=RecognitionResult.model_validate(rec_result),
                translation=translation_out,
                control=ComputerControlPayload.model_validate(cc_payload),
                phrase_status=phrase_status_out,
                echo_id=resp_echo,
                ts=now_ts,
            ).model_dump(exclude_none=True)

            await manager.send(session_id, server_msg)

    except WebSocketDisconnect:
        pass
    except Exception as loop_err:
        log.exception("ws_sign fatal error session=%s err=%s", session_id, loop_err)
    finally:
        manager.disconnect(session_id)
