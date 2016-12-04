import aws.entity.MetricAlarm
import aws.api.SNS
import aws.api.CloudWatch
import re

class LogMetricFilter:
    def __init__(self, logMetricFilterDict):
        self.name = logMetricFilterDict['filterName']
        self.filterPattern = logMetricFilterDict['filterPattern']
        self.metricTransformations = logMetricFilterDict['metricTransformations']

    def isUnauthorizedOperationFilter(self):
        return self._checkFilterIs('\s*({?)\s*(\(?)\$.errorCode\s*=\s*\"\*UnauthorizedOperation\"\s*(\)?)\s*(}?)\s*')

    def isAccessDeniedFilter(self):
        return self._checkFilterIs('\s*({?)\s*(\(?)\$.errorCode\s*=\s*\"AccessDenied\*\"\s*(\)?)\s*(}?)\s*')

    def isLoginWithoutMfaFilter(self):
        return self._checkFilterIs('\s*{\s*\$.userIdentity.sessionContext.attributes.mfaAuthenticated\s*!=\s*\"true\"\s*}\s*')

    def fetchAlarmsWithSubscribers(self):
        metricAlarms = []
        for metricTransformation in self.metricTransformations:
            cloudwatchAlarm = aws.api.CloudWatch().getAlarms(metricTransformation['metricName'], metricTransformation['metricNamespace'])['MetricAlarms']
            metricAlarms = metricAlarms + cloudwatchAlarm
        self.alarms = []
        for metricAlarmDict in metricAlarms:
            alarm = aws.entity.MetricAlarm(metricAlarmDict)
            if alarm.actions != []:
                for action in alarm.actions:
                    subscriptions = aws.api.SNS().getSubscriptions(action)['Subscriptions']
                    if subscriptions != []:
                        self.alarms.append(aws.entity.MetricAlarm(metricAlarmDict))

    def _checkFilterIs(self, filterRegex):
        occurences = re.findall(filterRegex, self.filterPattern)
        if occurences != []:
            return True
        else:
            return False