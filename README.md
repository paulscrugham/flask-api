# Demo Flask API

This project demonstrates a RESTful Flask API that utilizes Google Cloud Build and Datastore and OAuth using Auth0.

#
## Final Project: API Spec

CS 493: Cloud Application Development

Spring 2022

Oregon State University

API and account creation URL: [https://myapiurl.com/](https://myapiurl.com/)

[Datastore Data Model 2](#_Toc106551128)

[Create a Boat (protected) 3](#_Toc106551129)

[View a Boat (protected) 5](#_Toc106551130)

[View all Boats (protected) 7](#_Toc106551131)

[Update (replace) a Boat (protected) 10](#_Toc106551132)

[Update (modify) a Boat (protected) 12](#_Toc106551133)

[Delete a Boat (protected) 14](#_Toc106551134)

[Create a Load 16](#_Toc106551135)

[View a Load 18](#_Toc106551136)

[View all Loads 20](#_Toc106551137)

[Update (replace) a Load 23](#_Toc106551138)

[Update (modify) a Load 25](#_Toc106551139)

[Delete a Load 27](#_Toc106551140)

[Add a Load to a Boat (protected) 29](#_Toc106551141)

[Remove a Load from a Boat (protected) 31](#_Toc106551142)

# Datastore Data Model

The app stores three kinds of entities in Datastore: Users, Ships and Containers. If the required field is marked &quot;n/a&quot;, then the attribute is automatically added by the API.

## Users

| **Property** | **Data Type** | **Required?** | **Valid Examples** |
| --- | --- | --- | --- |
| id | Integer | n/a | 5748403989258 |
| name | String | Yes | &quot;Big Ship Shipping&quot; |

## Boats

| **Property** | **Data Type** | **Required?** | **Valid Examples** |
| --- | --- | --- | --- |
| id | Integer | n/a | 5839203948572 |
| name | String | Yes | &quot;Evergreen&quot; |
| length | Integer | Yes | 150 |
| date\_built | String | Yes | &quot;10-09-2022&quot; |
| owner | Integer | Yes | 5748403989258 |
| loads | List of ID Integers | Yes | [4602261653159936, 9385930294956] |
| self | String | n/a | https://myapiurl.com/5839203948572 |

## Loads

| **Property** | **Data Type** | **Required?** | **Valid Examples** |
| --- | --- | --- | --- |
| id | Integer | n/a | 4859203957185 |
| volume | Integer | Yes | 500 |
| carrier | Integer ID or null | Yes | 5839203948572 or Null |
| item | String | Yes | &quot;Shoes&quot; |
| creation\_date | String | Yes | &quot;10-09-2022&quot; |
| self | String | n/a | https://myapiurl.com/4859203957185 |

## Relationship Between Non-User Entities

The non-user entities are Boats and Loads. A Boat entity has a &quot;loads&quot; attribute which holds a list of load IDs that it is currently carrying. A Load entity has a &quot;carrier&quot; attribute which holds the ID of the Boat carrying the Load, or Null if it is not being carried.

## How the User Entity is Modelled

The User entity represents companies or owners of the Boats. A User entity has a &quot;Boats&quot; attribute which contains a list of all the Boat IDs which a User owns. The unique identifier for a User that is stored in Google Datastore is the JWT &quot;sub&quot; attribute. This makes it easy to check if an incoming request is authorized to access a particular resource. Every request to a protected resource must supply the &quot;id\_token&quot; of a JWT.

# Create a Boat (protected)

Allows you to create a new boat.

| POST /boats |
| --- |

## Request

### Path Parameters

None

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |
| Authorization | Bearer \&lt;id\_token\&gt; | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| name | The name of the boat. | Yes |
| date\_built | The date that the boat was constructed. | Yes |
| length | Length of the boat in feet. | Yes |

### Request Body Example

| {&quot;name&quot;: &quot;Sea Witch&quot;,&quot;date\_built&quot;: &quot;10-09-2022&quot;,&quot;length&quot;: 28} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 201 Created |
 |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

- Datastore will automatically generate an ID and store it with the entity being created. The ID will be added to the response.
- The app also generates a &quot;self&quot; URL that is provided in the response.
- Loads on the Boat are stored as IDs in Datastore, and the representation is generated for the response.

#### Success

| Status: 201 Created{&quot;date\_built&quot;: &quot;10-09-2022&quot;,&quot;loads&quot;: [{&quot;id&quot;: 5224275996835840,&quot;item&quot;: &quot;LEGO Blocks&quot;,&quot;self&quot;: &quot;https://myapiurl.com/loads/5224275996835840&quot;}],&quot;length&quot;: 28,&quot;name&quot;: &quot;Sea Witch&quot;,&quot;owner&quot;: &quot;auth0|62ad3c8e5639f8d4ad21ad19&quot;,&quot;id&quot;: 5843605314863104,&quot;self&quot;: &quot;https://myapiurl.com/boats/5843605314863104&quot;} |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){&quot;Error&quot;: &quot;Invalid header. Use an RS256 signed JWT Access Token&quot;} |
| --- |
| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |
| Status: 406 Not Acceptable{&quot;Error&quot;: &quot;The MIME type of the request object is not accepted&quot;} |

# View a Boat (protected)

Allows you to get an existing Boat.

| GET /boats/:boat\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| boat\_id | ID of the Boat |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |
| Authorization | Bearer \&lt;id\_token\&gt; | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/boats/5670392840585216

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK{&quot;date\_built&quot;: &quot;11-01-1999&quot;,&quot;loads&quot;: [{&quot;id&quot;: 4551752837758976,&quot;item&quot;: &quot;DUPLO&quot;,&quot;self&quot;: &quot;https://myapiurl.com/loads/4551752837758976&quot;},{&quot;id&quot;: 5224275996835840,&quot;item&quot;: &quot;Kinects&quot;,&quot;self&quot;: &quot;https://myapiurl.com/loads/5224275996835840&quot;}],&quot;length&quot;: 500,&quot;name&quot;: &quot;Patches The Boat&quot;,&quot;owner&quot;: &quot;auth0|62ad3c8e5639f8d4ad21ad19&quot;,&quot;id&quot;: 5843605314863104,&quot;self&quot;: &quot;https://myapiurl.com/boats/5843605314863104&quot;} |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){&quot;Error&quot;: &quot;Invalid header. Use an RS256 signed JWT Access Token&quot;} |
| --- |
| Status: 403 Forbidden{&quot;Error&quot;: &quot;This boat is owned by someone else.&quot;} |
| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |
| Status: 406 Not Acceptable{&quot;Error&quot;: &quot;The MIME type of the request object is not accepted&quot;} |

# View all Boats (protected)

List all the Boats for a particular User using pagination. If limit and offset are omitted, they default to limit=5 and offset=0.

| GET /boatsorGET /boats?limit=INT&amp;offset=INT |
| --- |

## Request

### Path Parameters

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| limit | Number of results to display | No |
| offset | Position to start displaying results | No |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |
| Authorization | Bearer \&lt;id\_token\&gt; | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/boats?limit=5&amp;offset=0

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK
{&quot;boats&quot;: [{&quot;date\_built&quot;: &quot;01-11-1925&quot;,&quot;owner&quot;: &quot;auth0|62ad3c8e5639f8d4ad21ad19&quot;,&quot;name&quot;: &quot;The Next Boat&quot;,&quot;loads&quot;: [],&quot;length&quot;: 14,&quot;id&quot;: 5280655361441792,&quot;self&quot;: &quot;https://myapiurl.com/boats/5280655361441792&quot;},{&quot;name&quot;: &quot;Patches The Boat&quot;,&quot;date\_built&quot;: &quot;11-01-1999&quot;,&quot;loads&quot;: [{&quot;id&quot;: 4551752837758976,&quot;item&quot;: &quot;DUPLO&quot;,&quot;self&quot;: &quot;https://myapiurl.com/loads/4551752837758976&quot;},{&quot;id&quot;: 5224275996835840,&quot;item&quot;: &quot;Kinects&quot;,&quot;self&quot;: &quot;https://myapiurl.com/loads/5224275996835840&quot;}],&quot;length&quot;: 500,&quot;owner&quot;: &quot;auth0|62ad3c8e5639f8d4ad21ad19&quot;,&quot;id&quot;: 5843605314863104,&quot;self&quot;: &quot;https://myapiurl.com/boats/5843605314863104&quot;}]} |
| --- |

####

#### Failure

| Status: 401 Unauthenticated (invalid JWT){&quot;Error&quot;: &quot;Invalid header. Use an RS256 signed JWT Access Token&quot;} |
| --- |
| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |
| Status: 406 Not Acceptable
{&quot;Error&quot;: &quot;The MIME type of the request object is not accepted&quot;} |

# Update (replace) a Boat (protected)

Allows you to replace an existing Boat&#39;s attributes with new values. Removes all Loads currently on the Boat.

| PUT /boats/:boat\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| boat\_id | ID of the Boat |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |
| Authorization | Bearer \&lt;id\_token\&gt; | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| name | The name of the boat. | Yes |
| date\_built | The date that the boat was constructed. | Yes |
| length | Length of the boat in feet. | Yes |

### Request Body Example

| {&quot;volume&quot;: 5,&quot;item&quot;: &quot;LEGO Blocks&quot;,&quot;creation\_date&quot;: &quot;10-18-2021&quot;} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK{&quot;date\_built&quot;: &quot;10-09-2022&quot;,&quot;loads&quot;: [],&quot;length&quot;: 28,&quot;name&quot;: &quot;Sea Witch&quot;,&quot;owner&quot;: &quot;auth0|62ad3c8e5639f8d4ad21ad19&quot;,&quot;id&quot;: 5843605314863104,&quot;self&quot;: &quot;https://myapiurl.com/boats/5843605314863104&quot;} |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){&quot;Error&quot;: &quot;Invalid header. Use an RS256 signed JWT Access Token&quot;} |
| --- |
| Status: 403 Forbidden{&quot;Error&quot;: &quot;This boat is owned by someone else.&quot;} |
| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |
| Status: 406 Not Acceptable{&quot;Error&quot;: &quot;The MIME type of the request object is not accepted&quot;} |

# Update (modify) a Boat (protected)

Allows you to modify a Boat&#39;s attributes individually. Any valid Load IDs provided in the &quot;loads&quot; attribute will add that Load to the Boat.

| PATCH /loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| name | The name of the boat. | No |
| date\_built | The date that the boat was constructed. | No |
| length | Length of the boat in feet. | No |
| loads | Valid Load IDs to add to the Boat. | No |

### Request Body Example

| {&quot;name&quot;: &quot;Patches The Boat&quot;,&quot;loads&quot;: [5224275996835840]} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |
| --- |
| Status: 406 Not Acceptable{&quot;Error&quot;: &quot;The MIME type of the request object is not accepted&quot;} |

# Delete a Boat (protected)

Allows you to delete a boat. The &quot;carrier&quot; attribute of any Loads currently on the Boat will be updated to null.

| DELETE /boats/:boat\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| boat\_id | ID of the boat |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Authorization | Bearer \&lt;id\_token\&gt; | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/boats/5670392840585216

## Response

### Response Body Format

Success: No body

Failure: JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content |
 |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){&quot;Error&quot;: &quot;Invalid header. Use an RS256 signed JWT Access Token&quot;} |
| --- |
| Status: 403 Forbidden{&quot;Error&quot;: &quot;This boat is owned by someone else.&quot;} |
| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |

# Create a Load

Allows you to create a new load.

| POST /loads |
| --- |

## Request

### Path Parameters

None

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| volume | The number of the Load. | Yes |
| item | A description of the item in the Load. | Yes |
| creation\_date | Date the Load was created. | Yes |

### Request Body Example

| {&quot;volume&quot;: 5,&quot;item&quot;: &quot;LEGO Blocks&quot;,&quot;creation\_date&quot;: &quot;10-18-2021&quot;} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 201 Created |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

- Datastore will automatically generate an ID and store it with the entity being created. This value will be added to the response body at the time of the request.
- The app also generates a &quot;self&quot; URL that is provided in the response.
- The value of the attribute carrier is represented as an object with the ID, name, and URL of the Boat that the Load is currently on. If not loaded, carrier should be null.

#### Success

| Status: 201 Created{&quot;carrier&quot;: null&quot;volume&quot;: 45,&quot;item&quot;: &quot;Kinects&quot;,&quot;creation\_date&quot;: &quot;01-01-2000&quot;,&quot;id&quot;: 5224275996835840,&quot;self&quot;: &quot;https://myapiurl.com/loads/5224275996835840&quot;} |
| --- |

#### Failure

| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |
| --- |
| Status: 406 Not Acceptable
{&quot;Error&quot;: &quot;The MIME type of the request object is not accepted&quot;} |

# View a Load

Allows you to get an existing Load.

| GET /loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/loads/4602261653159936

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK
{&quot;volume&quot;: 5,&quot;item&quot;: &quot;LEGO Blocks&quot;,&quot;carrier&quot;: {&quot;self&quot;: &quot;https://hw4-scrughap.wl.r.appspot.com/boats/5353126425001984&quot;,&quot;id&quot;: &quot;5353126425001984&quot;,&quot;name&quot;: &quot;Sea Witch&quot;},&quot;creation\_date&quot;: &quot;10/18/2021&quot;,&quot;id&quot;: 4602261653159936,&quot;self&quot;: &quot;https://hw4-scrughap.wl.r.appspot.com/loads/4602261653159936&quot;} |
| --- |

#### Failure

| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |
| --- |
| Status: 406 Not Acceptable{&quot;Error&quot;: &quot;The MIME type of the request object is not accepted&quot;} |

# View all Loads

List all the Loads using pagination. If limit and offset are omitted, they default to limit=5 and offset=0.

| GET /loadsorGET /loads?limit=INT&amp;offset=INT |
| --- |

## Request

### Path Parameters

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| limit | Number of results to display | No |
| offset | Position to start displaying results | No |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/loads?limit=5&amp;offset=0

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK{&quot;loads&quot;: [{&quot;carrier&quot;: null,&quot;volume&quot;: 60,&quot;item&quot;: &quot;Load #3&quot;,&quot;creation\_date&quot;: &quot;02-27-1991&quot;,&quot;id&quot;: 4548029034004480,&quot;self&quot;: &quot;https://myapiurl.com/loads/4548029034004480&quot;},{&quot;item&quot;: &quot;DUPLO&quot;,&quot;creation\_date&quot;: &quot;04-12-1985&quot;,&quot;carrier&quot;: {&quot;id&quot;: 5843605314863104,&quot;name&quot;: &quot;Patches The Boat&quot;,&quot;self&quot;: &quot;https://myapiurl.com/boats/5843605314863104&quot;},&quot;volume&quot;: 500,&quot;id&quot;: 4551752837758976,&quot;self&quot;: &quot;https://myapiurl.com/loads/4551752837758976&quot;},{&quot;item&quot;: &quot;Load #4&quot;,&quot;creation\_date&quot;: &quot;02-27-1991&quot;,&quot;volume&quot;: 60,&quot;carrier&quot;: null,&quot;id&quot;: 4999180384731136,&quot;self&quot;: &quot;https://myapiurl.com/loads/4999180384731136&quot;},{&quot;creation\_date&quot;: &quot;01-01-2000&quot;,&quot;carrier&quot;: null&quot;volume&quot;: 45,&quot;item&quot;: &quot;Kinects&quot;,&quot;id&quot;: 5224275996835840,&quot;self&quot;: &quot;https://myapiurl.com/loads/5224275996835840&quot;},{&quot;creation\_date&quot;: &quot;02-27-1991&quot;,&quot;item&quot;: &quot;Load #6&quot;,&quot;volume&quot;: 60,&quot;carrier&quot;: null,&quot;id&quot;: 5677652744601600,&quot;self&quot;: &quot;https://myapiurl.com/loads/5677652744601600&quot;}],&quot;next&quot;: &quot;https://myapiurl.com/loads?limit=5&amp;offset=5&quot;} |
| --- |

#### Failure

| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |
| --- |
| Status: 406 Not Acceptable{&quot;Error&quot;: &quot;The MIME type of the request object is not accepted&quot;} |

# Update (replace) a Load

Allows you to replace an existing Load&#39;s attributes with new values.

**NOTE: This endpoint does**  **not**  **modify the Load&#39;s &quot;carrier&quot; attribute.**

| PUT /loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| volume | The number of the Load. | Yes |
| item | A description of the item in the Load. | Yes |
| creation\_date | Date the Load was created. | Yes |

### Request Body Example

| {&quot;volume&quot;: 5,&quot;item&quot;: &quot;LEGO Blocks&quot;,&quot;creation\_date&quot;: &quot;10-18-2021&quot;} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK{&quot;carrier&quot;: null&quot;volume&quot;: 45,&quot;item&quot;: &quot;Kinects&quot;,&quot;creation\_date&quot;: &quot;01-01-2000&quot;,&quot;id&quot;: 5224275996835840,&quot;self&quot;: &quot;https://myapiurl.com/loads/5224275996835840&quot;} |
| --- |

#### Failure

| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |
| --- |
| Status: 406 Not Acceptable
{&quot;Error&quot;: &quot;The MIME type of the request object is not accepted&quot;} |

# Update (modify) a Load

Allows you to modify a Load&#39;s attributes individually.

**NOTE: This endpoint does**  **not**  **modify the Load&#39;s &quot;carrier&quot; attribute.**

| PATCH /loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| volume | The number of the Load. | No |
| item | A description of the item in the Load. | No |
| creation\_date | Date the Load was created. | No |

### Request Body Example

| {&quot;volume&quot;: 500} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |
| --- |
| Status: 406 Not Acceptable{&quot;Error&quot;: &quot;The MIME type of the request object is not accepted&quot;} |

# Delete a Load

Allows you to delete a Load. If the Load being deleted is currently on a Boat, the Load will also be removed from the Boat&#39;s &quot;loads&quot; attribute list.

**NOTE: If the Load to be deleted has a carrier, only the User who owns the carrier/boat can delete this load since it requires modification of a Boat (protected resource).**

| DELETE /loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the load |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Authorization | Bearer \&lt;id\_token\&gt; | Dependent on carrier status |

### Request Body

None

### Request URL example

https://myapiurl.com/loads/4602261653159936

## Response

### Response Body Format

Success: No body

Failure: JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content |
 |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){&quot;Error&quot;: &quot;Invalid header. Use an RS256 signed JWT Access Token&quot;} |
| --- |
| Status: 403 Forbidden{&quot;Error&quot;: &quot;This boat is owned by someone else.&quot;} |
| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |

# Add a Load to a Boat (protected)

Adds a Load to a Boat. A Load can only be on one Boat at a time.

| PUT /boats/:boat\_id/loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |
| boat\_id | ID of the Boat |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Authorization | Bearer \&lt;id\_token\&gt; | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/boats/5670392840585216/loads/4602261653159936

## Response

### Response Body Format

Success: No body

Failure: JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content | Succeeds only if a boat exists with this boat\_id, a load exists with this load\_id and the load is not on another boat. |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){&quot;Error&quot;: &quot;Invalid header. Use an RS256 signed JWT Access Token&quot;} |
| --- |
| Status: 403 Forbidden{&quot;Error&quot;: &quot;This boat is owned by someone else.&quot;} |
| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |

# Remove a Load from a Boat (protected)

A Load is removed from a Boat.

| DELETE /boats/:boat\_id/loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |
| boat\_id | ID of the Boat |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Authorization | Bearer \&lt;id\_token\&gt; | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/boats/5670392840585216/loads/4602261653159936

## Response

### Response Body Format

Success: No body

Failure: JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content | Succeeds only if a boat exists with this boat\_id, a load exists with this load\_id and this boat is at this load. |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){&quot;Error&quot;: &quot;Invalid header. Use an RS256 signed JWT Access Token&quot;} |
| --- |
| Status: 403 Forbidden{&quot;Error&quot;: &quot;This boat is owned by someone else.&quot;} |
| Status: 405 Method Not Allowed{&quot;Error&quot;: &quot;Method not recognized.&quot;} |

Page **46** of **46**