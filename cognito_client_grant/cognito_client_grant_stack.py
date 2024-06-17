from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_cognito as cognito,
    aws_iam as iam,
    CfnOutput as outputs,
)
from constructs import Construct
import random

class CognitoClientGrantStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Cognito User Pools
        user_pool1 = cognito.UserPool(self, "UserPoolDemo1",
                                     custom_attributes={
                                         "clientref": cognito.StringAttribute(
                                             mutable=False
                                         )
                                     })

        user_pool2 = cognito.UserPool(self, "UserPoolDemo2",
                                     custom_attributes={
                                         "clientref": cognito.StringAttribute(
                                             mutable=False
                                         )
                                     })

        scope_name = '*'
        full_access_scope = cognito.ResourceServerScope(
            scope_name=scope_name,
            scope_description='Full access'
        )

        resource_path = 'activity'
        res_server1 = user_pool1.add_resource_server(
            'ResourceServer',
            identifier=resource_path,
            scopes=[full_access_scope]
        )

        res_server2 = user_pool2.add_resource_server(
            'ResourceServer',
            identifier=resource_path,
            scopes=[full_access_scope]
        )


        #create cognito user pool domain name
        user_pool1.add_domain(
            'CognitoClient1Grant654987',
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix='userpool1clientgrant654987'
            )
        )    

        #create cognito user pool domain name
        user_pool2.add_domain(
            'CognitoClient2Grant654987',
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix='userpool2clientgrant654987'
            )
        )    


        
        # Add an app client with the client credential grant flow
        user_pool1_app = user_pool1.add_client(
            "app-client1", 
            generate_secret=True,
            o_auth=cognito.OAuthSettings(flows=cognito.OAuthFlows(client_credentials=True),
                                          scopes=[cognito.OAuthScope.resource_server(res_server1, full_access_scope)]
                                          ),
            #supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
            auth_flows=cognito.AuthFlow(user_password=True)
        )

        user_pool2_app = user_pool2.add_client(
            "app-client2", 
            generate_secret=True,
            o_auth=cognito.OAuthSettings(flows=cognito.OAuthFlows(client_credentials=True),
                                          scopes=[cognito.OAuthScope.resource_server(res_server2, full_access_scope)]
                                          ),
            #supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
            auth_flows=cognito.AuthFlow(user_password=True)
        )
    
        
        # Create the Lambda function
        lambda_function = lambda_.Function(
            self, "LambdaFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("cognito_client_grant/lambda")
        )

        # Grant invoke permissions to the API Gateway
        lambda_function.grant_invoke(iam.ServicePrincipal("apigateway.amazonaws.com"))

        # Configure OAuth settings for API Gateway authorizer
        oauth_settings = cognito.OAuthSettings(
            scopes=[cognito.OAuthScope.resource_server(res_server1, full_access_scope),cognito.OAuthScope.resource_server(res_server2, full_access_scope)],
            flows=cognito.OAuthFlows(
                client_credentials=True
            )
        )


        # Create the API Gateway with Cognito Authorizer  
        api = apigateway.LambdaRestApi(
            self, "Api", 
            handler=lambda_function,
            default_method_options=apigateway.MethodOptions(
                authorization_type=apigateway.AuthorizationType.COGNITO,
                authorizer=apigateway.CognitoUserPoolsAuthorizer(
                    self, "CognitoAuthorizer",
                    cognito_user_pools=[user_pool1,user_pool2]
                ),
                authorization_scopes=["activity/*"]
            )
        )

        #prepare the output to run queries
        myEnvVarOutputs = '\n\nexport API_URL={}\n\
            export TOKEN_URL1={}\n\
            export TOKEN_URL2={}\n\
            export CLIENT_ID1={}\n\
            export CLIENT_SECRET1={}\n\
            export CLIENT_ID2={}\n\
            export CLIENT_SECRET2={}\n\
            export AUTH1=$(echo -n "$CLIENT_ID1:$CLIENT_SECRET1" | base64)\n\
            export AUTH2=$(echo -n "$CLIENT_ID2:$CLIENT_SECRET2" | base64)'.format(api.url,
                                                                                     'https://userpool1clientgrant654987.auth.eu-west-1.amazoncognito.com/oauth2/token',
                                                                                     'https://userpool2clientgrant654987.auth.eu-west-1.amazoncognito.com/oauth2/token',
                                                                                     user_pool1_app.user_pool_client_id,
                                                                                     user_pool1_app.user_pool_client_secret.unsafe_unwrap(),
                                                                                     user_pool2_app.user_pool_client_id,
                                                                                     user_pool2_app.user_pool_client_secret.unsafe_unwrap())

        myTokenCommands ='\n\nrun curl --url $TOKEN_URL1 --header "Authorization: Basic $AUTH1" --header "Content-Type: application/x-www-form-urlencoded" --data-urlencode "grant_type=client_credentials" --data-urlencode "scope=activity/*"\n\n\
            copy the token by running BEARER1=bearervalue\n\n\
        run curl --url $TOKEN_URL2 --header "Authorization: Basic $AUTH2" --header "Content-Type: application/x-www-form-urlencoded" --data-urlencode "grant_type=client_credentials" --data-urlencode "scope=activity/*"\n\n\
            copy the token by running BEARER2=bearervalue\n\n'

        myAPIGWcommand= '\n\n you can finally test your commands running\n\
            curl --url $API_URL --header "Authorization: Bearer $BEARER1"\n\
            or\n\
            curl --url $API_URL --header "Authorization: Bearer $BEARER2"'
        # Outputs
        outputs(self, "output commands",
                value=myEnvVarOutputs+myTokenCommands+myAPIGWcommand,
                description="Export profiles for your shell")

                
