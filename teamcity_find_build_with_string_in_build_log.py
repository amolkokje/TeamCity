import os, urllib2, base64, ssl, re, time
import xml.etree.ElementTree as ET

SSL_CONTEXT = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
SSL_CONTEXT.options |= ssl.OP_NO_SSLv2
SSL_CONTEXT.options |= ssl.OP_NO_SSLv3

###########################################################################
## CUSTOMIZE THIS SECTION FOR YOUR NEEDS
###########################################################################

"""
USAGE
set the environment variables with your user credentials. These are required to set.
e.g. 
set TEAMCITY_SERVER=<>
set TEAMCITY_PORT=<>
set TEAMCITY_USERNAME=<>
set TEAMCITY_PASSWORD=<>
"""

# Specify the string containing substring of the build config of interest. This is a required variable to set. 
BUILD_CONFIG_LIKE = '' 

# This is the string to look for in the build log. This is a required variable to set. 
STRING_TO_LOOK = 'Failed'


"""
CODE LOGIC:
- get a list of all build configs using: http:<TEAMCITY-SERVER>:<TEAMCITY-PORT>/app/rest/buildTypes/
- find all the buildType (build configs) that contain the name, extract the 'id' information
- get all the builds for that build configuration using:
    - finished builds: http://<TEAMCITY-SERVER>:<TEAMCITY-PORT>/app/rest/builds/?locator=state:finished,start:0,count:100000,buildType:<BUILD-CONFIG-ID>
    - all builds: http://<TEAMCITY-SERVER>:<TEAMCITY-PORT>/app/rest/builds/?locator=start:0,count:100000,buildType:<BUILD-CONFIG-ID>
    --> http://<TEAMCITY-SERVER>:<TEAMCITY-PORT>/app/rest/builds/?locator=state:finished,start:0,count:100000,buildType:<BUILD-ID>
- get the build id from all the output
- for all the finished builds, you can get the raw build log output using: https://<TEAMCITY-SERVER>:<TEAMCITY-PORT>/downloadBuildLog.html?buildId=<BUILD-ID>&plain=true
- you can get the build webpage using the link: https://<TEAMCITY-SERVER>:<TEAMCITY-PORT>/viewLog.html?buildTypeId=<BUILD-CONFIG-ID>&buildId=<BUILD-ID>
    --> https://<TEAMCITY-SERVER>:<TEAMCITY-PORT>/viewLog.html?buildTypeId=<BUILD-CONFIG>&buildId=<BUILD-ID>
"""


###########################################################################
## DO NOT CHANGE CODE BELOW
###########################################################################

TEAMCITY_SERVER = os.environ['TEAMCITY_SERVER']
TEAMCITY_PORT = os.environ['TEAMCITY_PORT']
TEAMCITY_USERNAME = os.environ['TEAMCITY_USERNAME']
TEAMCITY_PASSWORD = os.environ['TEAMCITY_PASSWORD']
TEAMCITY_URL = 'http://{0}:{1}'.format(TEAMCITY_SERVER, TEAMCITY_PORT)


def execute_web_request(cmd):
    request = urllib2.Request(cmd)
    base64string = base64.encodestring('%s:%s' % (TEAMCITY_USERNAME, TEAMCITY_PASSWORD)).replace('\n', '')
    request.add_header('Authorization', 'Basic %s' % base64string)
    return urllib2.urlopen(request, context=SSL_CONTEXT).read()    


def execute_teamcity_rest_api(cmd):
    return execute_web_request('{0}/{1}'.format(TEAMCITY_URL, cmd))
    

def get_build_configs(build_config_like):
    build_configs = execute_teamcity_rest_api('app/rest/buildTypes/')    
    build_configs_like = filter(lambda c: build_config_like in c.attrib['id'], ET.fromstring(build_configs))
    return [build_config.attrib['id'] for build_config in build_configs_like]
    
    
def get_all_finished_build_ids(build_config_id, max_count=100000):
    finished_builds = execute_teamcity_rest_api('app/rest/builds/?locator=state:finished,start:0,count:{0},buildType:{1}'.format(max_count, build_config_id))
    return [finished_build.attrib['id'] for finished_build in ET.fromstring(finished_builds)]
    
    
def get_build_log(build_id):
    return execute_teamcity_rest_api('downloadBuildLog.html?buildId={0}&plain=true'.format(build_id))
    
    
if __name__ == '__main__':
    if not (TEAMCITY_USERNAME and TEAMCITY_PASSWORD and TEAMCITY_SERVER and TEAMCITY_PORT):
        raise RuntimeError('Username/Password/Server/Port not set as environment params!')

    if not (BUILD_CONFIG_LIKE and STRING_TO_LOOK):
        raise RuntimeError('Required search variables are not set!')

    print 'Looking for string in build log: {0}'.format(STRING_TO_LOOK)
    for build_config_id in get_build_configs(BUILD_CONFIG_LIKE):
        print "\nBUILD_CONFIG={0}".format(build_config_id)
        build_ids = get_all_finished_build_ids(build_config_id)        
        for build_id in build_ids:
            if STRING_TO_LOOK in get_build_log(build_id):
                print 'Found Build: https://{0}/viewLog.html?buildTypeId={1}&buildId={2}'.format(TEAMCITY_SERVER, build_config_id, build_id)                
  
    
