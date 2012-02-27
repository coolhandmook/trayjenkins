import mox
from unittest import TestCase
from pyjenkins.interfaces import IJenkinsFactory
from pyjenkins.jenkins import Jenkins
from pyjenkins.job import Job, JobStatus
from pyjenkins.server import Server

from trayjenkins.event import Event, IEvent
from trayjenkins.jobs import *

class JobsPresenterTests(TestCase):

    def test_Constructor_ModelFiresJobsUpdatedEvent_ViewSetJobsCalled(self):

        mocks= mox.Mox()

        jobs = 'list of jobs'
        model= mocks.CreateMock(IModel)
        view= mocks.CreateMock(IView)
        event= Event()

        model.jobsUpdatedEvent().AndReturn(event)
        view.setJobs(jobs)

        mocks.ReplayAll()

        presenter= Presenter(model, view)
        event.fire(jobs)

        mox.Verify(view)


class JobsModelTests(TestCase):

    def setUp(self):
        
        self.mocks = mox.Mox()
        self.jenkins = self.mocks.CreateMock(Jenkins)
        self.factory = self.mocks.CreateMock(IJenkinsFactory)
        self.event = self.mocks.CreateMock(IEvent)
        self.server = Server('host', 'uname', 'pw')

    def test_updateJobs_FirstCall_FireJobsUpdatedEventWithRetrievedJobs(self):

        jobs = [Job('job1', JobStatus.OK), Job('job2', JobStatus.FAILING)]
        self.factory.create(self.server).AndReturn(self.jenkins)
        self.jenkins.list_jobs().AndReturn(jobs)
        self.event.fire(jobs)
        self.mocks.ReplayAll()

        model = Model(self.server, self.factory, self.event)
        model.updateJobs()

        mox.Verify(self.event)

    def test_updateJobs_SecondCallReturnsSameJobs_JobsUpdatedEventNotFiredOnceOnly(self):

        jobs = [Job('job1', JobStatus.OK), Job('job2', JobStatus.FAILING)]
        self.factory.create(self.server).AndReturn(self.jenkins)
        self.jenkins.list_jobs().AndReturn(jobs)
        self.jenkins.list_jobs().AndReturn(jobs)
        self.event.fire(jobs)
        self.mocks.ReplayAll()

        model = Model(self.server, self.factory, self.event)
        model.updateJobs()
        model.updateJobs()

        mox.Verify(self.event)

    def test_updateJobs_SecondCallReturnsDifferentJobs_JobsUpdatedEventFiredForEachResult(self):

        jobsOne = [Job('job1', JobStatus.OK), Job('job2', JobStatus.FAILING)]
        jobsTwo = [Job('job1', JobStatus.OK), Job('job2', JobStatus.OK)]
        self.factory.create(self.server).AndReturn(self.jenkins)
        self.jenkins.list_jobs().AndReturn(jobsOne)
        self.jenkins.list_jobs().AndReturn(jobsTwo)
        self.event.fire(jobsOne)
        self.event.fire(jobsTwo)
        self.mocks.ReplayAll()

        model = Model(self.server, self.factory, self.event)
        model.updateJobs()
        model.updateJobs()

        mox.Verify(self.event)

    def test_jobsUpdatedEvent_ReturnsEventFromConstructor(self):

        self.factory.create(mox.IgnoreArg()).AndReturn(None)
        self.mocks.ReplayAll()

        model = Model(self.server, self.factory, self.event)

        self.assertTrue(self.event is model.jobsUpdatedEvent())


class NoFilterTests(TestCase):

    def test_filter_ReturnUnmodifiedList(self):

        jobs = ['list', 'of', 'jobs']
        filter = NoFilter()
        result = filter.filter(jobs)

        self.assertTrue(jobs is result)


class IgnoreJobsFilterTests(TestCase):

    def test_filter_NothingIgnored_ReturnUnmodifiedList(self):

        jobs = [Job('eric', JobStatus.FAILING),
                Job('terry', JobStatus.FAILING)]

        filter = IgnoreJobsFilter()
        result = filter.filter(jobs)

        self.assertEqual(jobs, result)

    def test_filter_EricIgnored_ReturnFilteredList(self):

        jobs = [Job('eric', JobStatus.FAILING),
                Job('terry', JobStatus.FAILING)]

        filter = IgnoreJobsFilter()
        filter.ignore('terry')

        expected = [Job('eric', JobStatus.FAILING)]
        result = filter.filter(jobs)

        self.assertEqual(expected, result)

    def test_filter_EricAndTerryIgnored_ReturnEmptyList(self):

        jobs = [Job('eric', JobStatus.FAILING),
                Job('terry', JobStatus.FAILING)]

        filter = IgnoreJobsFilter()
        filter.ignore('eric')
        filter.ignore('terry')

        expected = []
        result = filter.filter(jobs)

        self.assertEqual(expected, result)

    def test_filter_EricIgnoredThenUnignored_ReturnFilteredList(self):

        jobs = [Job('eric', JobStatus.FAILING),
                Job('terry', JobStatus.FAILING)]

        filter = IgnoreJobsFilter()
        filter.ignore('terry')
        filter.unignore('terry')

        result = filter.filter(jobs)

        self.assertEqual(jobs, result)

    def test_ignoring_JobNotIgnored_ReturnFalse(self):

        filter = IgnoreJobsFilter()

        result = filter.ignoring('norwegian blue')

        self.assertEqual(False, result)

    def test_ignoring_JobIsIgnored_ReturnTrue(self):

        filter = IgnoreJobsFilter()
        filter.ignore('norwegian blue')

        result = filter.ignoring('norwegian blue')

        self.assertEqual(True, result)
