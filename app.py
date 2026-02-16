import boto3
import botocore.config
import json

from datetime import datetime

#Funciton to generate blog
def blog_generate_using_bedrock(blogtopic:str)-> str:
    prompt=f"""Write a 200 words blog on {blogtopic}"""

    body={
        "prompt":prompt,
        "max_gen_len":512,#Tokens llama uses for words
        "temperature":0.5,
        "top_p":0.9
    }

    try:
        bedrock=boto3.client(
            "aws-bedrock-",
            region_name="ap-south-1",
            config=botocore.config.Config(
                read_timeout=300,#Lamda Timeout
                retries={'max_attempts':3}
            )
        )

        response=bedrock.invoke_model(
            body=json.dumps(body),
            modelId="meta.llama3-8b-instruct-v1:0",#Foundation-Model
            contentType="application/json",#Pass blog topic in json format
            accept="application/json"
        )

        response_content=response.get('body').read()
        response_data=json.loads(response_content)
        print(response_data)

        blog_details=response_data['generation']
        return blog_details

    except Exception as e:
        print(f"Error generating the blog:{e}")
        return ""

#Saving the details onto a Bucket
def save_blog_details_s3(s3_key,s3_bucket,generate_blog):
    s3=boto3.client('s3')

    try:#Content would be saved in the bucket, keypath provided in main function
        s3.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=generate_blog
        )
        print("Code saved to s3")

    except Exception as e:
        print("Code didn't save to S3")


def lambda_handler(event, context):
    event=json.loads(event['body'])
    blogtopic=event['blog_topic']

    generate_blog=blog_generate_using_bedrock(blogtopic=blogtopic)

    if generate_blog:
        current_time=datetime.now().strftime('%H%M%S')
        s3_key=f"blog-output/{current_time}.txt"
        s3_bucket='aws-bedrock-anki'
        save_blog_details_s3(s3_key,s3_bucket,generate_blog)

    else:
        print("No blog was generated")

    return{
        'statusCode':200,
        'body':json.dumps('Blog Generation is completed')
    }