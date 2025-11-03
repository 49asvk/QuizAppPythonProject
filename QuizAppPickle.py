# Importing needed libraries for this app.

# tkinter for GUI implementation
import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import pickle
import os


class Question:
    def __init__(self, question_text, choices, correct_choice):
        self.question_text = question_text
        self.choices = choices
        self.correct_choice = correct_choice

    def is_correct(self, user_choice):
        return self.correct_choice == user_choice


def load_questions(filename="questions.pkl"):
    try:
        with open(filename, "rb") as file:
            questions = pickle.load(file)
        return questions
    except FileNotFoundError:
        return []


def save_questions(questions, filename="questions.pkl"):
    with open(filename, "wb") as file:
        pickle.dump(questions, file)


def save_leaderboard(scores, filename="leaderboard.pkl"):
    with open(filename, "wb") as file:
        pickle.dump(scores, file)


def load_leaderboard(filename="leaderboard.pkl"):
    try:
        with open(filename, "rb") as file:
            scores = pickle.load(file)
        return scores
    except FileNotFoundError:
        return []


class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Application")
        self.root.geometry("600x400")
        
        self.current_question = 0
        self.score = 0
        self.timer = 15
        self.timer_running = False
        self.questions = []
        
        self.main_menu()

    def main_menu(self):
        """Displays the main menu options."""
        self.clear_screen()
        
        self.menu_label = tk.Label(self.root, text="Quiz Application", font=("Arial", 20))
        self.menu_label.pack(pady=20)
        
        self.create_button = tk.Button(self.root, text="Create Question Series", command=self.create_question_series, font=("Arial", 14))
        self.create_button.pack(pady=10)

        self.start_button = tk.Button(self.root, text="Start Quiz", command=self.select_question_series, font=("Arial", 14))
        self.start_button.pack(pady=10)

        self.leaderboard_button = tk.Button(self.root, text="View Leaderboard", command=self.view_leaderboard, font=("Arial", 14))
        self.leaderboard_button.pack(pady=10)

        self.quit_button = tk.Button(self.root, text="Quit", command=self.root.quit, font=("Arial", 14))
        self.quit_button.pack(pady=10)

    def clear_screen(self):
        """Clears the current widgets from the screen."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_question_series(self):
        """Allows user to create a custom question series."""
        self.clear_screen()
        
        self.series_name = simpledialog.askstring("Series Name", "Enter a name for the question series:")
        if not self.series_name:
            self.main_menu()
            return

        self.questions = []
        self.add_question()

    def add_question(self):
        """Prompts user to add a question to the series."""
        question_text = simpledialog.askstring("New Question", "Enter the question:")
        choices = [simpledialog.askstring("Choice", f"Enter choice {i+1}:") for i in range(4)]
        correct_choice = simpledialog.askinteger("Correct Answer", "Enter the correct choice number (1-4):") - 1

        if question_text and all(choices) and 0 <= correct_choice < 4:
            question = Question(question_text, choices, correct_choice)
            self.questions.append(question)
            
            more = messagebox.askyesno("Add Another?", "Do you want to add another question?")
            if more:
                self.add_question()
            else:
                save_questions(self.questions, f"{self.series_name}.pkl")
                messagebox.showinfo("Saved", f"Series '{self.series_name}' saved successfully!")
                self.main_menu()
        else:
            messagebox.showerror("Error", "Invalid question format. Please try again.")
            self.add_question()

    def select_question_series(self):
        """Allows user to select a saved question series."""
        self.clear_screen()
        
        series_files = [f for f in os.listdir() if f.endswith(".pkl") and f != "leaderboard.pkl"]
        if not series_files:
            messagebox.showinfo("No Series", "No question series found. Please create one first.")
            self.main_menu()
            return
        
        self.selected_series = tk.StringVar()
        self.selected_series.set(series_files[0])

        tk.Label(self.root, text="Select a Question Series:", font=("Arial", 14)).pack(pady=10)
        for series in series_files:
            tk.Radiobutton(self.root, text=series.replace(".pkl", ""), variable=self.selected_series, value=series).pack(anchor="w")
        
        tk.Button(self.root, text="Start", command=self.start_quiz, font=("Arial", 14)).pack(pady=20)
    
    def start_quiz(self):
        """Loads the selected series and starts the quiz."""
        self.questions = load_questions(self.selected_series.get())
        if not self.questions:
            messagebox.showerror("Error", "Failed to load questions.")
            self.main_menu()
            return
        
        self.current_question = 0
        self.score = 0
        self.show_question()

    def show_question(self):
        """Displays the current question."""
        self.clear_screen()
        
        if self.current_question < len(self.questions):
            self.timer = 15
            self.timer_running = True
            self.update_timer()
            
            question = self.questions[self.current_question]
            tk.Label(self.root, text=f"Q{self.current_question + 1}: {question.question_text}", font=("Arial", 14), wraplength=550).pack(pady=10)

            self.options = tk.IntVar()
            for i, choice in enumerate(question.choices):
                tk.Radiobutton(self.root, text=choice, variable=self.options, value=i, font=("Arial", 12)).pack(anchor="w")

            tk.Button(self.root, text="Submit", command=self.submit_answer, font=("Arial", 12)).pack(pady=10)
        else:
            self.end_quiz()

    def update_timer(self):
        """Updates the timer for the current question."""
        if self.timer > 0 and self.timer_running:
            self.timer -= 1
            self.root.after(1000, self.update_timer)
        elif self.timer == 0:
            self.timer_running = False
            messagebox.showinfo("Time's Up!", "Time's up for this question!")
            self.next_question()

    def submit_answer(self):
        """Validates the answer and updates the score."""
        if not self.timer_running:
            return

        self.timer_running = False
        user_choice = self.options.get()
        question = self.questions[self.current_question]
        
        if question.is_correct(user_choice):
            self.score += 1
            messagebox.showinfo("Correct!", "Correct answer!")
        else:
            messagebox.showerror("Incorrect", f"Correct answer was: {question.choices[question.correct_choice]}")
        
        self.next_question()

    def next_question(self):
        """Moves to the next question."""
        self.current_question += 1
        self.show_question()

    def end_quiz(self):
        """Ends the quiz and saves the score."""
        username = simpledialog.askstring("Quiz Completed", f"Your score: {self.score}/{len(self.questions)}\nEnter your name for the leaderboard:")
        if username:
            scores = load_leaderboard()
            scores.append((username, self.score))
            scores.sort(key=lambda x: x[1], reverse=True)
            save_leaderboard(scores[:10])
        
        self.main_menu()

    def view_leaderboard(self):
        """Displays the leaderboard with top scores."""
        self.clear_screen()
        
        tk.Label(self.root, text="Leaderboard", font=("Arial", 20)).pack(pady=10)
        scores = load_leaderboard()
        
        for rank, (username, score) in enumerate(scores, start=1):
            tk.Label(self.root, text=f"{rank}. {username}: {score}", font=("Arial", 14)).pack()

        tk.Button(self.root, text="Back to Menu", command=self.main_menu, font=("Arial", 14)).pack(pady=10)


# Main Application
if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
