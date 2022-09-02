FROM public.ecr.aws/lambda/python:3.8

ARG PROJECT
ARG ENV

ENV project=$PROJECT
ENV env=$ENV

# Install the function's dependencies using file requirements.txt
COPY lambda/setup_okta_integration/requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function specific files
COPY lambda/setup_okta_integration/client.py ${LAMBDA_TASK_ROOT}
COPY lambda/setup_okta_integration/lambda.py ${LAMBDA_TASK_ROOT}

COPY shared ${LAMBDA_TASK_ROOT}/shared

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda.handler" ]