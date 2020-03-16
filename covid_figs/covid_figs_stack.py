from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_events as events,
    aws_events_targets as targets,
)

class CovidFigsStack(core.Stack):

    def get_context(self, name):
        val = self.node.try_get_context(name)
        assert val, f"{name} context variable is not defined"
        return val
    
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket_name = self.get_context("bucket_name")
        bucket_prefix = self.get_context("bucket_prefix")

        # Defines an AWS Lambda resource
        covid_figs_lambda = _lambda.Function(
            self, 'CovidFigsHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda_build'),
            handler='covid_figs.handler',
            timeout=core.Duration.minutes(1),
            memory_size=256,
            environment={
                'NSP_S3_BUCKET_NAME': bucket_name,
                'NSP_S3_PREFIX': bucket_prefix
            }
        )
        
        # Configure Lambda Role
        events_bucket = s3.Bucket.from_bucket_name(
            self, 'EventsBucket',
            bucket_name
        )
        key_pattern = bucket_prefix + '*'
        events_bucket.grant_read_write(covid_figs_lambda, objects_key_pattern=key_pattern)
        events_bucket.grant_public_access(key_prefix=key_pattern)

        # Schedule 
        events.Rule(
            self, 'ScheduleRule',
            schedule=events.Schedule.expression('cron(0/15 18-19 * * ? *)'),
            targets=[targets.LambdaFunction(covid_figs_lambda)]
        )