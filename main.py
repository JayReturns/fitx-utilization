from requests import get, post
from dotenv import load_dotenv
import os
import logging
import time

load_dotenv()

HA_TOKEN = os.getenv('HA_TOKEN')
HA_URL = os.getenv('HA_URL')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
INTERVAL = int(os.getenv('INTERVAL', 3600))

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

studios = {
  'sensor.jim': '1561099930',
  'sensor.backup_jim': '1587147290',
  'sensor.mainz_jim': '1633404180'
}

def getUtilization(sensor):
  logger.debug(f'Fetching utilization for studio: {sensor}')
  utilization = get(f'https://mein.fitx.de/nox/public/v1/studios/{sensor}/utilization', headers={'x-tenant': 'fitx'})

  utilization.raise_for_status()
  items = utilization.json()['items']
  current = None
  for item in items:
    if item['isCurrent'] == True:
      current = item
      break

  percentage = current['percentage']
  logger.debug(f'Retrieved utilization: {percentage}% for studio {sensor}')
  return percentage

def send_to_home_assistant(sensor, percentage):
  logger.debug(f'Sending data to Home Assistant for {sensor}: {percentage}%')
  data = {
    'state': percentage,
    'attributes': {
      'friendly_name': sensor,
      'unit_of_measurement': '%',
      'icon': 'mdi:weight-lifter'
    }
  }

  response = post(f'{HA_URL}/api/states/{sensor}', 
                  headers={'Authorization': f'Bearer {HA_TOKEN}', 'content-type': 'application/json'},
                  json=data)
  response.raise_for_status()
  logger.debug(f'Successfully sent data to Home Assistant for {sensor}')
  return response

def main():
  logger.info(f'Starting FitX utilization monitor with {INTERVAL}s interval')
  while True:
    logger.info('Starting FitX utilization update')
    for sensor, studio_id in studios.items():
      try:
        percentage = getUtilization(studio_id)
        logger.info(f'{sensor}: {percentage}%')
        response = send_to_home_assistant(sensor, percentage)
        logger.info(f'Status: {response.status_code}')
      except Exception as e:
        logger.error(f'Error processing {sensor}: {e}')
    logger.info('Completed FitX utilization update')
    logger.debug(f'Sleeping for {INTERVAL} seconds')
    time.sleep(INTERVAL)

if __name__ == '__main__':
  main()