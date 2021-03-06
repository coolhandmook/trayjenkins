import mox
from unittest import TestCase

from trayjenkins.event import Event, IEvent
from trayjenkins.jobs import IModel as JobsModel, IFilter, JobModel
from trayjenkins.status import IModel, IView, Presenter, IMessageComposer,\
    IStatusReader, Model, StatusReader, DefaultMessageComposer
from pyjenkins.job import Job, JobStatus


class StatusPresenterTests(TestCase):

    def test_Constructor_ModelFiresStatusChangedEvent_ViewSetStatusCalled(self):

        mocks = mox.Mox()

        model = mocks.CreateMock(IModel)
        view = mocks.CreateMock(IView)
        event = Event()

        model.status_changed_event().AndReturn(event)
        view.set_status('some status string', 'status message')

        mocks.ReplayAll()

        presenter = Presenter(model, view)  # @UnusedVariable
        event.fire('some status string', 'status message')

        mox.Verify(view)


class StatusModelTests(TestCase):

    def setUp(self):

        self.mocks = mox.Mox()
        self.jobs_filter = self.mocks.CreateMock(IFilter)
        self.messageComposer = self.mocks.CreateMock(IMessageComposer)
        self.statusReader = self.mocks.CreateMock(IStatusReader)
        self.statusEvent = self.mocks.CreateMock(IEvent)
        self.jobsModel = self.mocks.CreateMock(JobsModel)
        self.jobsEvent = Event()
        self.jobsModel.jobs_updated_event().AndReturn(self.jobsEvent)
        self.jobs = [Job('who', 'cares?')]
        self.job_models = [JobModel(self.jobs[0], False)]

    def test_updateStatus_JobsModelFiresFirstUpdateEventStatusUnknownAndMessageNone_StatusChangedEventNotFired(self):

        self.jobs_filter.filter_jobs(self.job_models).AndReturn(self.job_models)
        self.messageComposer.message(self.jobs).AndReturn(None)
        self.statusReader.status(self.jobs).AndReturn(JobStatus.UNKNOWN)
        self.mocks.ReplayAll()

        model = Model(self.jobsModel,  # @UnusedVariable
                      self.jobs_filter,
                      self.messageComposer,
                      self.statusReader,
                      self.statusEvent)

        self.jobsEvent.fire(self.job_models)

        mox.Verify(self.statusEvent)

    def test_updateStatus_JobsModelFiresFirstUpdateEvent_StatusChangedEventFired(self):

        self.jobs_filter.filter_jobs(self.job_models).AndReturn(self.job_models)
        self.messageComposer.message(self.jobs).AndReturn('message')
        self.statusReader.status(self.jobs).AndReturn(JobStatus.FAILING)
        self.statusEvent.fire(JobStatus.FAILING, 'message')
        self.mocks.ReplayAll()

        model = Model(self.jobsModel,  # @UnusedVariable
                      self.jobs_filter,
                      self.messageComposer,
                      self.statusReader,
                      self.statusEvent)

        self.jobsEvent.fire(self.job_models)

        mox.Verify(self.statusEvent)

    def test_updateStatus_TwoJobsModelUpdatesWithSameStatusAndMessage_StatusChangedEventFiredOnce(self):

        self.jobs_filter.filter_jobs(self.job_models).AndReturn(self.job_models)
        self.jobs_filter.filter_jobs(self.job_models).AndReturn(self.job_models)
        self.messageComposer.message(self.jobs).AndReturn('message')
        self.messageComposer.message(self.jobs).AndReturn('message')
        self.statusReader.status(self.jobs).AndReturn(JobStatus.FAILING)
        self.statusReader.status(self.jobs).AndReturn(JobStatus.FAILING)
        self.statusEvent.fire(JobStatus.FAILING, 'message')
        self.mocks.ReplayAll()

        model = Model(self.jobsModel,  # @UnusedVariable
                      self.jobs_filter,
                      self.messageComposer,
                      self.statusReader,
                      self.statusEvent)

        self.jobsEvent.fire(self.job_models)
        self.jobsEvent.fire(self.job_models)

        mox.Verify(self.statusEvent)

    def test_updateStatus_TwoJobsModelUpdatesWithDifferentStatus_StatusChangedEventFiredTwice(self):

        self.jobs_filter.filter_jobs(self.job_models).AndReturn(self.job_models)
        self.jobs_filter.filter_jobs(self.job_models).AndReturn(self.job_models)
        self.messageComposer.message(self.jobs).AndReturn('message')
        self.messageComposer.message(self.jobs).AndReturn('message')
        self.statusReader.status(self.jobs).AndReturn(JobStatus.FAILING)
        self.statusReader.status(self.jobs).AndReturn(JobStatus.OK)
        self.statusEvent.fire(JobStatus.FAILING, 'message')
        self.statusEvent.fire(JobStatus.OK, 'message')
        self.mocks.ReplayAll()

        model = Model(self.jobsModel,  # @UnusedVariable
                      self.jobs_filter,
                      self.messageComposer,
                      self.statusReader,
                      self.statusEvent)

        self.jobsEvent.fire(self.job_models)
        self.jobsEvent.fire(self.job_models)

        mox.Verify(self.statusEvent)

    def test_updateStatus_TwoJobsModelUpdatesWithDifferentMessage_StatusChangedEventFiredTwice(self):

        self.jobs_filter.filter_jobs(self.job_models).AndReturn(self.job_models)
        self.jobs_filter.filter_jobs(self.job_models).AndReturn(self.job_models)
        self.messageComposer.message(self.jobs).AndReturn('message one')
        self.messageComposer.message(self.jobs).AndReturn('message two')
        self.statusReader.status(self.jobs).AndReturn(JobStatus.FAILING)
        self.statusReader.status(self.jobs).AndReturn(JobStatus.FAILING)
        self.statusEvent.fire(JobStatus.FAILING, 'message one')
        self.statusEvent.fire(JobStatus.FAILING, 'message two')
        self.mocks.ReplayAll()

        model = Model(self.jobsModel,  # @UnusedVariable
                      self.jobs_filter,
                      self.messageComposer,
                      self.statusReader,
                      self.statusEvent)

        self.jobsEvent.fire(self.job_models)
        self.jobsEvent.fire(self.job_models)

        mox.Verify(self.statusEvent)

    def test_updateStatus_JobsFilterReturnsModifiedList_ModifiedListPassedTo(self):

        filtered_jobs = [Job('completely', 'different')]
        filtered_models = [JobModel(filtered_jobs[0], True)]
        self.jobs_filter.filter_jobs(self.job_models).AndReturn(filtered_models)
        self.messageComposer.message(filtered_jobs).AndReturn('message')
        self.statusReader.status(filtered_jobs).AndReturn(JobStatus.OK)
        self.statusEvent.fire(JobStatus.OK, 'message')
        self.mocks.ReplayAll()

        model = Model(self.jobsModel,  # @UnusedVariable
                      self.jobs_filter,
                      self.messageComposer,
                      self.statusReader,
                      self.statusEvent)

        self.jobsEvent.fire(self.job_models)

        mox.Verify(self.statusEvent)


class StatusReaderTests(TestCase):

    def test_status_OneFailingJob_ReturnFailing(self):

        jobs = [Job('eric', JobStatus.UNKNOWN),
                Job('john', JobStatus.FAILING),
                Job('terry', JobStatus.OK),
                Job('graham', JobStatus.DISABLED)]

        reader = StatusReader()
        result = reader.status(jobs)

        self.assertEqual(JobStatus.FAILING, result)

    def test_status_NoFailingJobs_ReturnOk(self):

        jobs = [Job('eric', JobStatus.UNKNOWN),
                Job('terry', JobStatus.OK),
                Job('graham', JobStatus.DISABLED)]

        reader = StatusReader()
        result = reader.status(jobs)

        self.assertEqual(JobStatus.OK, result)

    def test_status_JobsListIsNone_ReturnUnknown(self):

        reader = StatusReader()
        result = reader.status(None)

        self.assertEqual(JobStatus.UNKNOWN, result)


class DefaultMessageComposerTests(TestCase):

    def test_message_EmptyJobs_ReturnCorrectMessage(self):

        jobs = []

        composer = DefaultMessageComposer()
        result = composer.message(jobs)

        self.assertEqual('No jobs', result)

    def test_message_AllJobsOk_ReturnCorrectMessage(self):

        jobs = [Job('eric', JobStatus.OK),
                Job('terry', JobStatus.OK)]

        composer = DefaultMessageComposer()
        result = composer.message(jobs)

        self.assertEqual('All active jobs pass', result)

    def test_message_OneFailingJob_ReturnCorrectMessage(self):

        jobs = [Job('eric', JobStatus.OK),
                Job('terry', JobStatus.FAILING)]

        composer = DefaultMessageComposer()
        result = composer.message(jobs)

        self.assertEqual('FAILING:\nterry', result)

    def test_message_TwoFailingJobs_ReturnCorrectMessage(self):

        jobs = [Job('eric', JobStatus.FAILING),
                Job('terry', JobStatus.FAILING)]

        composer = DefaultMessageComposer()
        result = composer.message(jobs)

        self.assertEqual('FAILING:\neric\nterry', result)

    def test_message_JobsListIsNone_ReturnUnknown(self):

        composer = DefaultMessageComposer()
        result = composer.message(None)

        self.assertEqual('', result)
