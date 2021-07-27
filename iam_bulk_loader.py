import boto3
import csv
import uuid
import envoy
from appscript import app,k

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--accountId', action='store', type=str, required=True)
parser.add_argument('--accountName', action='store', type=str, required=True)
parser.add_argument('--userList', action='store', type=str, required=True)
arguments = parser.parse_args()

iam = boto3.client("iam")
outlook = app("Microsoft Outlook")
account_id=arguments.accountId.strip()
account_name=arguments.accountName.strip()
def craft_email(recipient_name,recipient_email, pwpush_url):
    msg = outlook.make(
        new=k.outgoing_message,
        with_properties={
            k.subject: f"Your new AWS Account ({account_name})",
            k.plain_text_content: f"""
            Dear {recipient_name},
            You now have access to the AWS Management Console for {account_id}
            
            Login URL: https://{account_id}.signin.aws.amazon.com/console

            Username: {recipient_email}
            
            Password URL: {pwpush_url}

            During your first sign-in, you must change your password.

            Kind Regards,
            """
        }
    )
    msg.make(
        new=k.recipient,
        with_properties={
            k.email_address: {
                k.name: recipient_name,
                k.address: recipient_email
            }
        }
    )
    msg.open()
    msg.activate()

if __name__ == "__main__":
    with open(arguments.userList.strip()) as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            password = str(uuid.uuid4())
            # print(row)
            # print(row['Name'], row['Email'], row['Group'], password)
            real_name=row['Name'].strip()

            username = row["Email"].strip()
            iam.create_user(UserName=username)
            iam.create_login_profile(UserName=username, Password=password, PasswordResetRequired=True)
            iam.add_user_to_group(UserName=username, GroupName=row['Group'])
            pusher = envoy.run(f"curl -Ls -w %{{url_effective}} -o /dev/null 'https://pwpush.kainos.com/p' --data-raw 'utf8=✓&password[payload]={password}&commit=Push+it!'")
            password_url = pusher.std_out
            craft_email(recipient_name=real_name,recipient_email=username,pwpush_url=password_url)
    
