import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    asg = boto3.client('autoscaling')
    
    # Get all autoscaling groups
    response = asg.describe_auto_scaling_groups()
    for group in response['AutoScalingGroups']:
        group_name = group['AutoScalingGroupName']
        print(f"Processing autoscaling group: {group_name}")
        
        # Check if any instance has been running for more than an hour
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:aws:autoscaling:groupName', 'Values': [group_name]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_launch_time = instance['LaunchTime']
                instance_age = datetime.now(instance_launch_time.tzinfo) - instance_launch_time
                if instance_age > timedelta(hours=1):
                    print(f"Instance {instance['InstanceId']} has been running for more than an hour, scaling down group {group_name}...")
                    asg.update_auto_scaling_group(
                        AutoScalingGroupName=group_name,
                        MinSize=0,
                        MaxSize=0,
                        DesiredCapacity=0
                    )