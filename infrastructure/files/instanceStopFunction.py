import json
import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')
    
    allowed_uptime = 60
    all_instances = [instance.state["Name"] for instance in ec2_resource.instances.all()]
    number_of_running_instances = all_instances.count('running')
    
    running_instances = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'instance-state-code',
                'Values': ['16']
            }
        ]
    )
    
    for i in range(number_of_running_instances):
        try:
            format = "%Y-%m-%d %H:%M:%S"
            instance_launch_time = running_instances['Reservations'][i]['Instances'][0]['LaunchTime'].strftime(format)
            date_time_instance = datetime.strptime(instance_launch_time, format)
    
            now = datetime.now().strftime(format)
            date_time_now = datetime.strptime(now, format)
            print(date_time_instance)
            print(date_time_now)
            uptime = (date_time_now - date_time_instance).total_seconds() / 60
    
            print(uptime)
            if uptime >= allowed_uptime:
                instance_id = running_instances['Reservations'][i]['Instances'][0]['InstanceId']
                ec2_client.stop_instances(
                    InstanceIds=[
                        instance_id
                    ],
                    Force=True
                )
                print(f"{instance_id} is stopped")
        except:
            continue
