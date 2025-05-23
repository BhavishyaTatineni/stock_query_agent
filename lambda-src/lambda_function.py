import logging
import os
import sys

from mangum import Mangum

from app import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Mangum handler directly.
# This object will be invoked by AWS Lambda.
handler = Mangum(app)