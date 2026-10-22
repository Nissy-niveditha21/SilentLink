class SentenceBuilder:
    def __init__(self):
        self.current_word = ""
        self.sentence = ""

    def process_input(self, gesture):
        """
        Gesture classes expected:
        - A-Z letters
        - SPACE
        - DELETE
        - CLEAR
        - ENTER
        """

        if gesture == "SPACE":
            if self.current_word:
                self.sentence += self.current_word + " "
                self.current_word = ""

        elif gesture == "DELETE":
            self.current_word = self.current_word[:-1]

        elif gesture == "CLEAR":
            self.current_word = ""
            self.sentence = ""

        elif gesture == "ENTER":
            completed_sentence = self.sentence.strip()
            self.current_word = ""
            self.sentence = ""
            return completed_sentence

        else:
            self.current_word += gesture

        return None

    def get_display_text(self):
        return self.sentence + self.current_word
