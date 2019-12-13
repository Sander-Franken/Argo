import importlib
import json

argo = importlib.import_module('.Argo', 'Classes.Argo')


def handler(event, context):
	try:		
		result = argo.Argo(event).findLatLng()
		response_body = {
				"results": result,
				"error": {
					"has_error": False,
					"exceptionType": "",
					"exceptionMessage": ""
				}
			}

		return {
			"statusCode": 200,
			"body": json.dumps(response_body, ensure_ascii = False)
		}

	except Exception as e:
		exception_status_code = getExceptionStatusCode(e)
		exception_message = createExceptionMessage(e)
		response_body = {
				"results": {
					"foundMatch": False,
					"method": "",
					"result": ""
				},
				"error": exception_message
			}

		return {
			"statusCode": exception_status_code,
			"body": json.dumps(response_body, ensure_ascii = False)
		}


# Retrieves the status code for the custom exceptions. Returns 500 if an unexpected, built-in exception occurs.
def getExceptionStatusCode(e):
	exception_status_code = 500
	if len(e.args) > 1:						# Built-in exceptions.args contains only the message, so throws IndexError if we assume more
		exception_status_code = e.args[1]	

	return exception_status_code


# Constructs the error values for the return message. Works for both custom and built-in exceptions. For built-in exceptions the traceback
# is not included, only the message. They should not occur.
def createExceptionMessage(e):
	exception_type = e.__class__.__name__
	exception_content = e.args[0]

	exception_message = {
		"hasError": True,
		"exceptionType": exception_type,
		"exceptionMessage": exception_content
	}
	
	return exception_message
