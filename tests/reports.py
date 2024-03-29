import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from random import randint
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.contrib.auth.models import Permission

try:
    from django.utils import timezone
except ImportError:
    from timepiece import timezone

from timepiece.tests.base import TimepieceDataTestCase

from timepiece import models as timepiece
from timepiece import forms as timepiece_forms
from timepiece import utils


class ReportsHelperBase(TimepieceDataTestCase):
    def setUp(self):
        super(ReportsHelperBase, self).setUp()
        self.sick = self.create_project()
        self.vacation = self.create_project()
        settings.TIMEPIECE_PAID_LEAVE_PROJECTS = {
            'sick': self.sick.pk,
            'vacation': self.vacation.pk
        }
        self.leave = [self.sick.pk, self.vacation.pk]
        self.p1 = self.create_project(billable=True, name='1')
        self.p2 = self.create_project(billable=False, name='2')
        self.p4 = self.create_project(billable=True, name='4')
        self.p3 = self.create_project(billable=False, name='1')
        self.p5 = self.create_project(billable=True, name='3')
        self.default_projects = [self.p1, self.p2, self.p3, self.p4, self.p5]
        self.default_dates = [
            utils.add_timezone(datetime.datetime(2011, 1, 3)),
            utils.add_timezone(datetime.datetime(2011, 1, 4)),
            utils.add_timezone(datetime.datetime(2011, 1, 10)),
            utils.add_timezone(datetime.datetime(2011, 1, 16)),
            utils.add_timezone(datetime.datetime(2011, 1, 17)),
            utils.add_timezone(datetime.datetime(2011, 1, 18)),
        ]

    def make_entries(self, user=None, projects=None, dates=None,
                 hours=1, minutes=0):
        """Make several entries to help with reports tests"""
        if not user:
            user = self.user
        if not projects:
            projects = self.default_projects
        if not dates:
            dates = self.default_dates
        for project in projects:
            for day in dates:
                self.log_time(project=project, start=day,
                              delta=(hours, minutes), user=user)

    def bulk_entries(self, start=datetime.datetime(2011, 1, 2),
                   end=datetime.datetime(2011, 1, 4)):
        start = utils.add_timezone(start)
        end = utils.add_timezone(end)
        dates = utils.generate_dates(start, end, 'day')
        projects = [self.p1, self.p2, self.p2, self.p4, self.p5, self.sick]
        self.make_entries(projects=projects, dates=dates,
                          user=self.user, hours=2)
        self.make_entries(projects=projects, dates=dates,
                          user=self.user2, hours=1)

    def check_generate_dates(self, start, end, trunc, dates):
        for index, day in enumerate(utils.generate_dates(start, end, trunc)):
            if isinstance(day, datetime.datetime):
                day = day.date()
            self.assertEqual(day, dates[index].date())


class TestHourlyReport(ReportsHelperBase):
    def setUp(self):
        super(TestHourlyReport, self).setUp()
        self.url = reverse('hourly_report')

    def testGenerateMonths(self):
        dates = [utils.add_timezone(datetime.datetime(2011, month, 1))
            for month in xrange(1, 13)]
        start = datetime.date(2011, 1, 1)
        end = datetime.date(2011, 12, 1)
        self.check_generate_dates(start, end, 'month', dates)

    def testGenerateWeeks(self):
        dates = [
            utils.add_timezone(datetime.datetime(2010, 12, 27)),
            utils.add_timezone(datetime.datetime(2011, 01, 03)),
            utils.add_timezone(datetime.datetime(2011, 01, 10)),
            utils.add_timezone(datetime.datetime(2011, 01, 17)),
            utils.add_timezone(datetime.datetime(2011, 01, 24)),
            utils.add_timezone(datetime.datetime(2011, 01, 31)),
        ]
        start = utils.add_timezone(datetime.datetime(2011, 1, 1))
        end = utils.add_timezone(datetime.datetime(2011, 2, 1))
        self.check_generate_dates(start, end, 'week', dates)

    def testGenerateDays(self):
        dates = [utils.add_timezone(datetime.datetime(2011, 1, day))
            for day in xrange(1, 32)]
        start = utils.add_timezone(datetime.datetime(2011, 1, 1))
        end = utils.add_timezone(datetime.datetime(2011, 1, 31))
        self.check_generate_dates(start, end, 'day', dates)

    def check_truncs(self, trunc, billable, non_billable):
        self.make_entries(user=self.user)
        self.make_entries(user=self.user2)
        entries = timepiece.Entry.objects.date_trunc(trunc)
        for entry in entries:
            if entry['billable']:
                self.assertEqual(entry['hours'], billable)
            else:
                self.assertEqual(entry['hours'], non_billable)

    def testTruncMonth(self):
        self.check_truncs('month', 18, 12)

    def testTruncWeek(self):
        self.check_truncs('week', 6, 4)

    def testTruncDay(self):
        self.check_truncs('day', 3, 2)

    def get_project_totals(self, date_headers, trunc, query=Q(),
                           hour_type='total'):
        """Helper function for testing project_totals utility directly"""
        entries = timepiece.Entry.objects.date_trunc(trunc).filter(query)
        if entries:
            pj_totals = utils.project_totals(entries, date_headers, hour_type)
            pj_totals = list(pj_totals)
            rows = pj_totals[0][0]
            hours = [hours for name, user_id, hours in rows]
            totals = pj_totals[0][1]
            return hours, totals
        else:
            return ''

    def log_daily(self, start, day2, end):
        self.log_time(project=self.p1, start=start, delta=(1, 0))
        self.log_time(project=self.p1, start=day2, delta=(0, 30))
        self.log_time(project=self.p3, start=day2, delta=(1, 0))
        self.log_time(project=self.p1, start=day2, delta=(3, 0),
                      user=self.user2)
        self.log_time(project=self.sick, start=end, delta=(2, 0),
                      user=self.user2)

    def testDailyTotal(self):
        start = utils.add_timezone(datetime.datetime(2011, 1, 1))
        day2 = utils.add_timezone(datetime.datetime(2011, 1, 2))
        end = utils.add_timezone(datetime.datetime(2011, 1, 3))
        self.log_daily(start, day2, end)
        trunc = 'day'
        date_headers = utils.generate_dates(start, end, trunc)
        pj_totals = self.get_project_totals(date_headers, trunc)
        self.assertEqual(pj_totals[0][0],
                         [Decimal('1.00'), Decimal('1.50'), ''])
        self.assertEqual(pj_totals[0][1],
                         ['', Decimal('3.00'), Decimal('2.00')])
        self.assertEqual(pj_totals[1],
                         [Decimal('1.00'), Decimal('4.50'), Decimal('2.00')])

    def testBillableNonBillable(self):
        start = utils.add_timezone(datetime.datetime(2011, 1, 1))
        day2 = utils.add_timezone(datetime.datetime(2011, 1, 2))
        end = utils.add_timezone(datetime.datetime(2011, 1, 3))
        self.log_daily(start, day2, end)
        trunc = 'day'
        billableQ = Q(project__type__billable=True)
        non_billableQ = Q(project__type__billable=False)
        date_headers = utils.generate_dates(start, end, trunc)
        pj_billable = self.get_project_totals(date_headers, trunc, Q(),
                                              'billable')
        pj_billable_q = self.get_project_totals(date_headers, trunc, billableQ,
                                                'total')
        pj_non_billable = self.get_project_totals(date_headers, trunc, Q(),
                                                  'non_billable')
        pj_non_billable_q = self.get_project_totals(date_headers, trunc,
                                                    non_billableQ, 'total')
        self.assertEqual(list(pj_billable), list(pj_billable_q))
        self.assertEqual(list(pj_non_billable), list(pj_non_billable_q))

    def testWeeklyTotal(self):
        start = utils.add_timezone(datetime.datetime(2011, 1, 3))
        end = utils.add_timezone(datetime.datetime(2011, 1, 6))
        self.bulk_entries(start, end)
        trunc = 'week'
        date_headers = utils.generate_dates(start, end, trunc)
        pj_totals = self.get_project_totals(date_headers, trunc)
        self.assertEqual(pj_totals[0][0], [48])
        self.assertEqual(pj_totals[0][1], [24])
        self.assertEqual(pj_totals[1], [72])

    def testMonthlyTotal(self):
        start = utils.add_timezone(datetime.datetime(2011, 1, 1))
        end = utils.add_timezone(datetime.datetime(2011, 3, 1))
        trunc = 'month'
        last_day = randint(5, 10)
        worked1 = randint(1, 3)
        worked2 = randint(1, 3)
        for month in xrange(1, 7):
            for day in xrange(1, last_day + 1):
                day = utils.add_timezone(datetime.datetime(2011, month, day))
                self.log_time(start=day, delta=(worked1, 0), user=self.user)
                self.log_time(start=day, delta=(worked2, 0), user=self.user2)
        date_headers = utils.generate_dates(start, end, trunc)
        pj_totals = self.get_project_totals(date_headers, trunc)
        for hour in pj_totals[0][0]:
            self.assertEqual(hour, last_day * worked1)
        for hour in pj_totals[0][1]:
            self.assertEqual(hour, last_day * worked2)

    def argsHelper(self, args={}, start=datetime.datetime(2011, 1, 2),
                   end=datetime.datetime(2011, 1, 4)):
        start = utils.add_timezone(start)
        end = utils.add_timezone(end)
        args.update({
            'from_date': start.strftime('%m/%d/%Y'),
            'to_date': end.strftime('%m/%d/%Y'),
            'export': True,
        })
        return args

    def makeTotals(self, args={}):
        """Return CSV from hourly report for verification in tests"""
        self.client.login(username='superuser', password='abc')
        response = self.client.get(self.url, args, follow=True)
        return [item.split(',') \
                for item in response.content.split('\r\n')][:-1]

    def checkTotals(self, args, data):
        """assert that project_totals contains the data passed in"""
        totals = self.makeTotals(args)
        for row, datum in zip(totals, data):
            self.assertEqual(row[1:], datum)

    def testForm_HourTypeFlags(self):
        """Verify that the billable, non-billable and paid leave flags work"""
        #Test paid leave
        self.bulk_entries()
        args = {
            'billable': True,
            'non_billable': True,
            'paid_leave': False,
            'trunc': 'week',
        }
        data = [
            ['12/27/2010', '01/03/2011', 'Total'],
            ['10.00', '20.00', '30.00'],
            ['5.00', '10.00', '15.00'],
            ['15.00', '30.00', '45.00'],
        ]
        args = self.argsHelper(args)
        self.checkTotals(args, data)
        #test billable
        args = {
            'billable': True,
            'non_billable': False,
            'paid_leave': False,
            'trunc': 'week',
        }
        data = [
            ['12/27/2010', '01/03/2011', 'Total'],
            ['6.00', '12.00', '18.00'],
            ['3.00', '6.00', '9.00'],
            ['9.00', '18.00', '27.00'],
        ]
        args = self.argsHelper(args)
        self.checkTotals(args, data)
        #test non_billable
        args = {
            'billable': False,
            'non_billable': True,
            'paid_leave': False,
            'trunc': 'week',
        }
        data = [
            ['12/27/2010', '01/03/2011', 'Total'],
            ['4.00', '8.00', '12.00'],
            ['2.00', '4.00', '6.00'],
            ['6.00', '12.00', '18.00'],
        ]
        args = self.argsHelper(args)
        self.checkTotals(args, data)

    def testForm_Day(self):
        args = {
            'billable': True,
            'non_billable': False,
            'paid_leave': False,
            'trunc': 'day',
        }
        data = [
            ['01/02/2011', '01/03/2011', '01/04/2011', 'Total'],
            ['6.00', '6.00', '6.00', '18.00'],
            ['3.00', '3.00', '3.00', '9.00'],
            ['9.00', '9.00', '9.00', '27.00'],
        ]
        self.bulk_entries()
        args = self.argsHelper(args)
        self.checkTotals(args, data)

    def testForm_Week(self):
        args = {
            'billable': True,
            'non_billable': True,
            'paid_leave': True,
            'trunc': 'week',
        }
        data = [
            ['12/27/2010', '01/03/2011', 'Total'],
            ['12.00', '24.00', '36.00'],
            ['6.00', '12.00', '18.00'],
            ['18.00', '36.00', '54.00'],
        ]
        self.bulk_entries()
        args = self.argsHelper(args)
        self.checkTotals(args, data)

    def testForm_Month(self):
        tz = timezone.get_current_timezone()
        start = datetime.datetime(2011, 1, 4, tzinfo=tz)
        end = datetime.datetime(2011, 3, 28, tzinfo=tz)
        args = {
            'billable': True,
            'non_billable': False,
            'paid_leave': False,
            'trunc': 'month',
        }
        data = [
            ['01/01/2011', '02/01/2011', '03/01/2011', 'Total'],
            ['168.00', '168.00', '168.00', '504.00'],
            ['84.00', '84.00', '84.00', '252.00'],
            ['252.00', '252.00', '252.00', '756.00'],
        ]
        self.bulk_entries(start, end)
        args = self.argsHelper(args, start, end)
        self.checkTotals(args, data)

    def testForm_Pj_Select(self):
        """Filter out hours just for one project"""
        #Test project 1
        self.bulk_entries()
        args = {
            'billable': True,
            'non_billable': True,
            'paid_leave': False,
            'trunc': 'day',
            'pj_select_1': self.p1.id,
        }
        data = [
            ['01/02/2011', '01/03/2011', '01/04/2011', 'Total'],
            ['2.00', '2.00', '2.00', '6.00'],
            ['1.00', '1.00', '1.00', '3.00'],
            ['3.00', '3.00', '3.00', '9.00'],
        ]
        args = self.argsHelper(args)
        self.checkTotals(args, data)
        #Test with project 2
        args = {
            'billable': True,
            'non_billable': True,
            'paid_leave': False,
            'trunc': 'day',
            'pj_select_1': self.p2.id
        }
        data = [
            ['01/02/2011', '01/03/2011', '01/04/2011', 'Total'],
            ['4.00', '4.00', '4.00', '12.00'],
            ['2.00', '2.00', '2.00', '6.00'],
            ['6.00', '6.00', '6.00', '18.00'],
        ]
        args = self.argsHelper(args)
        self.checkTotals(args, data)
        #Test with 2 project filters
        args = {
            'billable': True,
            'non_billable': True,
            'paid_leave': False,
            'trunc': 'day',
            'pj_select_1': [self.p2.id, self.p4.id]
        }
        data = [
            ['01/02/2011', '01/03/2011', '01/04/2011', 'Total'],
            ['6.00', '6.00', '6.00', '18.00'],
            ['3.00', '3.00', '3.00', '9.00'],
            ['9.00', '9.00', '9.00', '27.00'],
        ]
        args = self.argsHelper(args)
        self.checkTotals(args, data)

    def testNoPermission(self):
        """
        Regular users shouldn't be able to retrieve the hourly report
        page.

        """
        self.client.login(username='user', password='abc')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def testSuperUserPermission(self):
        """Super users should be able to retrieve the hourly report page."""
        self.client.login(username='superuser', password='abc')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def testEntrySummaryPermission(self):
        """
        If a regular user is given the view_entry_summary permission, they
        should be able to retrieve the hourly report page.

        """
        self.client.login(username='user', password='abc')
        entry_summ_perm = Permission.objects.get(codename='view_entry_summary')
        self.user.user_permissions.add(entry_summ_perm)
        self.user.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class TestBillableHours(ReportsHelperBase):
    def setUp(self):
        super(TestBillableHours, self).setUp()
        self.url = reverse('billable_hours')
        self.permission = Permission.objects.filter(
            codename='view_entry_summary'
        )
        self.admin = self.create_user('admin', 'e@e.com', 'abc')
        self.admin.user_permissions = self.permission
        self.from_date = datetime.datetime(2011, 1, 2)
        self.to_date = datetime.datetime(2011, 1, 4)
        self.dates_data = ['12/27/2010', '01/03/2011']

    def get_entries_data(self):
        projects = utils.get_setting('TIMEPIECE_PAID_LEAVE_PROJECTS')
        # Account for the day added by the form
        query = Q(end_time__gt=utils.get_week_start(self.from_date),
            end_time__lt=self.to_date + relativedelta(days=1))
        query &= ~Q(project__in=projects.values())
        entries = timepiece.Entry.objects.date_trunc('week',
            extra_values=('activity', 'project__status')).filter(query)
        return entries

    def test_access_permission(self):
        """
        You should be able to access the page if you have the
        correct permissions
        """
        self.client.login(username='admin', password='abc')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_access_no_permission(self):
        """A regular should have no access to the page"""
        self.client.login(username='user', password='abc')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_response_data(self):
        """Test that the data returned is correct"""
        self.bulk_entries()
        self.client.login(username='admin', password='abc')

        response = self.client.get(self.url, data={
            'from_date': self.from_date.strftime('%m/%d/%Y'),
            'to_date': self.to_date.strftime('%m/%d/%Y')
        })
        self.assertEqual(response.status_code, 200)

        entries_data = self.get_entries_data().order_by('user', 'date')
        response_data = json.loads(response.context['data'])
        dates = json.loads(response.context['dates'])

        self.assertEqual(dates, self.dates_data)

        for user, data in response_data.iteritems():
            last_name = user.strip()
            entries_total = sum([float(e['hours']) for e in
                entries_data.filter(user__last_name=last_name)])
            response_total = sum(e['total'] for e in data)
            self.assertEqual(entries_total, response_total)
