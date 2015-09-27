import urllib2
import ping
import requests
import time
import json
import logging


# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
config = {}
with open('config.json', 'r') as f:
    config = json.loads(f.read())
cachet_url = config['cachet_url']
ping_metric_id = config['ping_metric_id']
component_id = config['component_id']
token = config['token']
test_IP = config['test_IP']


def internet_status():
    """
    Get the internet connection status (Try to connect to an IP address).

    Returns:
        True if we have internet access, False otherwise.
    """
    try:
        urllib2.urlopen('http://{}'.format(test_IP), timeout=1)
        return True
    except:
        return False


def test_ping():
    """
    Get the average ping.

    Returns:
        The average ping in ms.
    """
    return ping.quiet_ping(test_IP, timeout=1000)[2]


def send_ping_to_cachet():
    """
    Send the ping to Cachet.
    """
    ping = test_ping()
    timestamp = int(time.time())
    headers = {'X-Cachet-Token': token}
    logger.info('Sending ping({})...'.format(ping))
    requests.post('{0}api/v1/metrics/{1}/points?value={2}&timestamp={3}'.format(
        cachet_url, ping_metric_id, ping, timestamp), headers=headers)


def get_last_incident_id():
    """
    Get the last incident id.

    Returns:
        Last incident id.
    """
    try:
        headers = {'X-Cachet-Token': token}

        data = requests.get(
            '{0}api/v1/incidents'.format(cachet_url), headers=headers).json()
        return data['data'][-1]['id']
    except:
        return None


def send_state_to_cachet():
    """
    Send the internet status to cachet. Is there is a problem create an incident.
    If it returns to normal, resolve incdent.
    """
    headers = {'X-Cachet-Token': token, 'content-type': 'application/json'}
    status = 1
    if not internet_status():
        logger.info('Sending incident...')
        status = 4
        data = {
            'name': 'outage',
            'message': 'Lost connection',
            'status': 1,
            'visible': 1
        }
        requests.post('{0}api/v1/incidents/'.format(cachet_url),
                      data=json.dumps(data), headers=headers)
    else:
        last_incident = get_last_incident_id()
        if last_incident is not None:
            logger.info('Fixing incident...')
            requests.put('{0}api/v1/incidents/{1}?status={2}'.format(cachet_url,
                                                                     last_incident, 4), headers=headers)

    logger.info('Sending state...')
    requests.put('{0}api/v1/components/{1}?status={2}'.format(cachet_url,
                                                              component_id, status), headers=headers)


if __name__ == "__main__":
    while True:
        send_ping_to_cachet()
        send_state_to_cachet()
        time.sleep(300)
