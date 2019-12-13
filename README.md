# Argo - Lat Long Retrieval 
---

## What is this service used for: 

Argo is used to detect coordinates in strings. It will return coordinates found in both Degrees Minutes Seconds (DMS) and Decimal notation.


#### Author:
[Sander Franken]()

## Connecting to the service:

#### Endpoint:
```
https://connect.globalinter.net/argo
```

#### Uris & Methods:

| Uri Path | Methods allowed |
| --- | --- |
| /detect | `HEAD` `POST` |


#### Security: 
An X-Api-Key is used for this API.


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

