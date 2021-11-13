import json
import urllib.parse
import boto3
import logging
import urllib3
import base64

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logger.debug('Loading function')

s3 = boto3.client('s3')


def detect_labels(bucket, photo):

    client=boto3.client('rekognition')
    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        MaxLabels=10)
    # response = client.detect_labels(Image={'Bytes': photo},
    #     MaxLabels=10)
    logger.debug(response)
    
    return response

def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        head_response = s3.head_object(Bucket=bucket, Key=key)
        logger.debug('HEAD RESPONSE_ANDY')
        logger.debug(head_response)
        # image_body = (s3.get_object(Bucket=bucket, Key=key)['Body']).read()
        # base64_image=base64.b64encode(image_body)
        # base_64_binary = base64.decodebytes(base64_image)
        
        logger.debug('BODY BELOW')
        logger.debug(key)
        rec_response = detect_labels(bucket, key)
        logger.debug(rec_response)
        
        customLabels = []
        
        try:
            customLabel_string = head_response['Metadata']['x-amz-meta-customlabels']
            customLabels = customLabel_string.split(',')
        except:
            customLabels = []
        
        print(head_response)

        
        print("CONTENT TYPE: " + head_response['ContentType'])
        print(head_response['LastModified'])
        tim = str(head_response['LastModified'])
        print(bucket)
        label_list = []
        for customLabel in customLabels:
            label_list.append(customLabel.strip())
        for label in rec_response['Labels']:
            label_list.append(label['Name'])

        print(label_list)
        logger.debug(head_response['ContentType'])
        
        http = urllib3.PoolManager()
        url = 'https://search-photos-pjxa5eqm4fy446tkhrfr5qw6o4.ap-southeast-1.es.amazonaws.com/photos/_doc/'
        url = url + key[:-4]
        d1 = {'objectKey': key, 'bucket': bucket, 'createdTimestamp': tim, 'labels': label_list}
        encoded_data = json.dumps(d1).encode('utf-8')
        HEADERS = {'Authorization': 'Basic YW5keWJpcmxhX3Bob3RvczpTd2F0aTI0MDcq', 'Content-Type': 'application/json'}
        result = http.request('PUT', url, body=encoded_data, headers = HEADERS)
        result = json.loads(result.data)
        print(result)
        logger.debug('Completed working!!!')
        
        return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,PUT'
        },
        'body': json.dumps('Hello from Lambda!')
    }
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
