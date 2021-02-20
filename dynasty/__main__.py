import sys

from dynasty.app import Application, MainWindow


app = Application(sys.argv)
window = MainWindow()

window.show()
sys.exit(app.exec_())
