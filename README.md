# Argo - Lat Long Retrieval 
---

## What is this service used for: 

Argo is used to detect coordinates in strings. It will return coordinates found in both Degrees Minutes Seconds (DMS) and Decimal notation. It is built to be deployed on Amazon Lambda, triggered through the API Gateway.

#### Author:
[Sander Franken](https://github.com/Sander-Franken)

#### How to set up this service:

- On AWS Lambda:
	If you're deploying this service on AWS Lambda all you need is the lambda_function.zip file.
	Create a new Lambda function with runtime Python 3.7, set the handler function to be lambda_function.handler and you're good to go! Further in this README you may find the required request format.

- Otherwise:
	You will likely not be using the lambda_function.py file and thus will have to restructure a bit. The main difference is in the instantiation of the Argo class in the "handler" method in the lambda_function.py file and the "fetchRequestBody" method in the Argo class. They refer to the "event" variable that is passed to the handler method by AWS Lambda. This is a JSON, where the "body" is the address that is supplied with the request. When not using AWS Lambda you must find your own way of getting the address into the self.address variable in the Argo class.



#### Request:
One single address should be provided per request.
The format is standard JSON.

- Headers:

| Key | Value |
| --- | --- |
| Content-Type  | application/json |
| X-Api-Key  | Your Api Key |


- Request Body:
```json
{
  	"address": "Apple Street 40, Lat: 24.567 Lng: -44.32, Banana Country"
}
```

#### Response:
The response is in JSON and divided in two parts:

 - The results, which will tell you whether a match was found and if so, what method got the result and the coordinates found. 

 - The errors, informing you if an exception occured during execution with the type and message accompanying it. Custom exception classes have been built for input validation, but this part of the JSON will also return if a built-in Python exception triggered. 

Example successful response from `/detect`: 
```json
{
	"results": {
		"foundMatch": true,
		"method": "Decimal",
		"result": [
			"24.567",
			"-44.32"
		]
	},
	"error": {
		"has_error": false,
		"exceptionType": "",
		"exceptionMessage": ""
	}
}
```
Example error response from `/detect`:
```json
{
    "results": {
        "foundMatch": false,
        "method": "",
        "result": ""
    },
    "error": {
        "hasError": true,
        "exceptionType": "noAddressValue",
        "exceptionMessage": "The address value supplied appears to be empty."
    }
}
```
Request Body used for this example:
```json
{
	"address":""
}
```

### Requirements/Caveats:
 - The service is built to parse addresses. You can give it any string as input and it will still try to find coordinates, but results may not be as accurate.
 - The underlying script uses a series of filters (RegEx) to fish out coordinates sequentially from strict to looser filters. If a filter gets a result, that result is returned and none of the looser filters that would otherwise be executed after this one will be used. By their nature DMS coordinates require a stricter filter than Decimal coordinates. Following from the previous: if the address put in contains both coordinates in DMS and Decimal notation only the coordinates in DMS will be returned.
 - Coordinates in Decimal notation really look just like any number with a decimal point. Sometimes addresses will contain regular numbers ex. for distances. The script uses some minor magic to attempt to filter out any regular numbers and only return coordinates, but it is not perfect. 

