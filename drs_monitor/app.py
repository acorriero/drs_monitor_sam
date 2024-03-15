import boto3

def lagged_source_servers(region):
    '''
    List all hosts that are falling behind
    '''
    result = []
    client = boto3.client('drs', region_name=region)

    response = client.describe_source_servers(
        filters={
            'stagingAccountIDs': []
        }
    )

    for i in response['items']:
        source_hostname = i['sourceProperties']['identificationHints']['hostname']
        source_rep_state = i['dataReplicationInfo']['dataReplicationState']
        if source_rep_state not in {'CONTINUOUS', 'CREATING_SNAPSHOT', 'INITIAL_SYNC'}:
            result.append({'hostname': source_hostname, 'rep_state': source_rep_state})
    
    return result

def format_output(source_servers):
    result = []
    for server in source_servers:
        result.append(
            f"DRS replication for host: {server['hostname']} is falling behind because of it's current state: {server['rep_state']}"
        )

    return result

def lambda_handler(event, context):
    region = 'us-west-2'
    source_servers = lagged_source_servers(region)
    # Format for email message
    email_message = "\n".join(format_output(source_servers))

    # Create a new AWS SNS client
    sns_client = boto3.client('sns')
    
    # Specify the topic ARN or topic name where you want to publish the message
    topic_arn = 'arn:aws:sns:us-east-1:${{env.Account}}:drs_replication_check'

    # Publish the message to the specified SNS topic
    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject='DRS Replication Lag',
            Message=email_message
        )
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")

