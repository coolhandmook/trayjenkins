import os
import sys
from optparse import OptionParser
from PySide import QtGui

import gui.fake
import gui.jobs
import gui.media
import gui.status

from trayjenkins.jobs import Model as JobsModel, Presenter as JobsPresenter
from trayjenkins.status import Model as StatusModel, StatusReader, Presenter as StatusPresenter
from pyjenkins.server import Server
from trayjenkins import __version__

class MainWindow(QtGui.QDialog):

    def __init__(self, jenkinsHost, mediaFiles):
        super(MainWindow, self).__init__()

        self.createActions()
        self.createJobsMVP(jenkinsHost, mediaFiles)
        self.createTrayIcon(mediaFiles)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.jobsView)
        self.setLayout(mainLayout)

        self.jobsUpdateTimer = gui.jobs.UpdateTimer(self.jobsModel, 5, self)

        self.setWindowTitle("TrayJenkins (%s)" % __version__)
        self.resize(640, 480)

    def createJobsMVP(self, jenkinsHost, mediaFiles):

        if jenkinsHost == 'FAKE':
            self.jobsModel = gui.fake.JobsModel()
        else:
            self.jobsModel = JobsModel(Server(jenkinsHost, '', ''))

        self.jobsView = gui.jobs.ListView(mediaFiles)
        self.jobsPresenter = JobsPresenter(self.jobsModel, self.jobsView)

    def createActions(self):

        self.quitAction = QtGui.QAction("&Quit", self, triggered=QtGui.qApp.quit)
        self.showControlsAction = QtGui.QAction("&Show controls", self, triggered=self.showNormal)

    def createTrayIcon(self, mediaFiles):

        self.trayMenu = QtGui.QMenu(self)
        self.trayMenu.addAction(self.showControlsAction)
        self.trayMenu.addAction(self.quitAction)

        self.trayIcon = QtGui.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayMenu)

        view = gui.status.MultiView([gui.status.TrayIconView(self.trayIcon, mediaFiles),
                                     gui.status.SoundView(self, mediaFiles)])
        self.statusModel = StatusModel(self.jobsModel, StatusReader())
        self.statusPresenter = StatusPresenter(self.statusModel, view)

    def closeEvent(self, event):
        self.hide()
        event.ignore()

class Application(QtGui.QDialog):

    def __init__(self):

        self.application= QtGui.QApplication(sys.argv)
        self.application.setApplicationName('Trayjenkins')

    def run(self):

        jenkinsHost = self.parseOptions()
        mediaFiles = gui.media.MediaFiles(self.executablePath())

        window = MainWindow(jenkinsHost, mediaFiles)

        return self.application.exec_()

    def parseOptions(self):

        parser = OptionParser(usage='usage: %prog [options] host')
        (options, args) = parser.parse_args()

        if len(args) is 1:
            jenkinsHost = args[0]
        else:
            parser.print_help()
            sys.exit(1)

        return jenkinsHost

    def executablePath(self):

        path = ''
        try:
            path = sys._MEIPASS
        except AttributeError:
            path = os.path.abspath(".")
            
        return path
