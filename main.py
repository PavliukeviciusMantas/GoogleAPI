import sys
from PyQt6 import QtWidgets, QtCore
from service.google_mail import GoogleMail


class GmailApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.gmail = GoogleMail()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Gmail API App")
        self.resize(800, 600)

        # Main layout
        layout = QtWidgets.QVBoxLayout(self)

        # Input fields for sending an email
        self.recipient_input = QtWidgets.QLineEdit(self)
        self.recipient_input.setPlaceholderText("Gavėjas (Recipient)")
        layout.addWidget(self.recipient_input)

        self.subject_input = QtWidgets.QLineEdit(self)
        self.subject_input.setPlaceholderText("Tema (Subject)")
        layout.addWidget(self.subject_input)

        self.message_input = QtWidgets.QTextEdit(self)
        self.message_input.setPlaceholderText("Žinutė (Message)")
        layout.addWidget(self.message_input)

        self.send_button = QtWidgets.QPushButton("Siųsti laišką", self)
        self.send_button.clicked.connect(self.send_email)
        layout.addWidget(self.send_button)

        # Search bar for filtering emails
        self.search_input = QtWidgets.QLineEdit(self)
        self.search_input.setPlaceholderText("Ieškoti laiškų...")
        self.search_input.textChanged.connect(self.filter_emails)
        layout.addWidget(self.search_input)

        # Table for displaying emails
        self.email_table = QtWidgets.QTableWidget(self)
        self.email_table.setColumnCount(4)
        self.email_table.setHorizontalHeaderLabels(["Siuntėjas", "Tema", "Žinutė", "Veiksmai"])
        self.email_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.email_table)

        # Refresh button
        self.refresh_button = QtWidgets.QPushButton("Atnaujinti (Refresh)", self)
        self.refresh_button.clicked.connect(self.load_emails)
        layout.addWidget(self.refresh_button)

        # Mark as read button
        self.mark_as_read_button = QtWidgets.QPushButton("Pažymėti kaip skaitytus", self)
        self.mark_as_read_button.clicked.connect(self.mark_as_read)
        layout.addWidget(self.mark_as_read_button)

        # Load emails into the table
        self.load_emails()

    def mark_as_read(self):
        """Mark unread emails as read."""
        try:
            query = "is:unread"  # Query to find unread emails
            messages_to_mark = self.gmail.search_messages(query)
            print(f"Matched emails: {len(messages_to_mark)}")
            if messages_to_mark:
                self.gmail.service.users().messages().batchModify(
                    userId='me',
                    body={
                        'ids': [msg['id'] for msg in messages_to_mark],
                        'removeLabelIds': ['UNREAD']
                    }
                ).execute()
                QtWidgets.QMessageBox.information(self, "Sėkmė", "Laiškai pažymėti kaip skaityti!")
                self.load_emails()  # Refresh the table after marking emails as read
            else:
                QtWidgets.QMessageBox.information(self, "Informacija", "Nėra laiškų, atitinkančių užklausą.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Klaida", f"Laiškų žymėjimas nepavyko: {e}")  

    def send_email(self):
        """Send an email using the Gmail API."""
        recipient = self.recipient_input.text().strip()
        subject = self.subject_input.text().strip()
        message = self.message_input.toPlainText().strip()

        if not recipient or not subject or not message:
            QtWidgets.QMessageBox.warning(self, "Klaida", "Visi laukai turi būti užpildyti!")
            return

        try:
            self.gmail.send_message(recipient, subject, message)
            QtWidgets.QMessageBox.information(self, "Sėkmė", "Laiškas išsiųstas sėkmingai!")
            self.recipient_input.clear()
            self.subject_input.clear()
            self.message_input.clear()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Klaida", f"Laiško siuntimas nepavyko: {e}")

    def load_emails(self):
        """Load emails into the table."""
        self.email_table.setRowCount(0)  # Clear the table
        try:
            messages = self.gmail.search_messages("")  # Fetch all messages
            for message in messages:
                data = self.gmail.read_message(message)
                row_position = self.email_table.rowCount()
                self.email_table.insertRow(row_position)

                # Extract email data
                sender = ""
                subject = ""
                snippet = data["snippet"]
                labels = data.get("labelIds", [])
                is_unread = "UNREAD" in labels

                for header in data["payload"]["headers"]:
                    if header["name"].lower() == "from":
                        sender = header["value"]

                subject = next((h["value"] for h in data["payload"]["headers"] if h["name"].lower() == "subject"), "(Be temos)")

                # Populate the table
                self.email_table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(sender))
                self.email_table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(subject))
                self.email_table.setItem(row_position, 2, QtWidgets.QTableWidgetItem(snippet))

                # Add delete button
                delete_button = QtWidgets.QPushButton("Ištrinti")
                delete_button.clicked.connect(lambda checked, msg=message: self.delete_email(msg))
                self.email_table.setCellWidget(row_position, 3, delete_button)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Klaida", f"Laiškų įkėlimas nepavyko: {e}")

    def filter_emails(self):
        """Filter emails based on the search input."""
        filter_text = self.search_input.text().lower()
        for row in range(self.email_table.rowCount()):
            match = False
            for column in range(self.email_table.columnCount() - 1):  # Exclude the "Veiksmai" column
                item = self.email_table.item(row, column)
                if item and filter_text in item.text().lower():
                    match = True
                    break
            self.email_table.setRowHidden(row, not match)

    def delete_email(self, message):
        """Delete an email using the Gmail API."""
        try:
            self.gmail.delete_message(message)
            QtWidgets.QMessageBox.information(self, "Sėkmė", "Laiškas ištrintas sėkmingai!")
            self.load_emails()  # Refresh the table
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Klaida", f"Laiško ištrynimas nepavyko: {e}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = GmailApp()
    window.show()
    sys.exit(app.exec())