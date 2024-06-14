import aws_cdk as core
import aws_cdk.assertions as assertions

from cognito_client_grant.cognito_client_grant_stack import CognitoClientGrantStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cognito_client_grant/cognito_client_grant_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CognitoClientGrantStack(app, "cognito-client-grant")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
