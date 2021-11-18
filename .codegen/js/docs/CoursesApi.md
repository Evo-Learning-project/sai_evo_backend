# SnippetsApi.CoursesApi

All URIs are relative to *http://127.0.0.1:8000*

Method | HTTP request | Description
------------- | ------------- | -------------
[**coursesCreate**](CoursesApi.md#coursesCreate) | **POST** /courses/ | 
[**coursesDelete**](CoursesApi.md#coursesDelete) | **DELETE** /courses/{id}/ | 
[**coursesEventsCreate**](CoursesApi.md#coursesEventsCreate) | **POST** /courses/{course_pk}/events/ | 
[**coursesEventsDelete**](CoursesApi.md#coursesEventsDelete) | **DELETE** /courses/{course_pk}/events/{id}/ | 
[**coursesEventsList**](CoursesApi.md#coursesEventsList) | **GET** /courses/{course_pk}/events/ | 
[**coursesEventsPartialUpdate**](CoursesApi.md#coursesEventsPartialUpdate) | **PATCH** /courses/{course_pk}/events/{id}/ | 
[**coursesEventsParticipationsCreate**](CoursesApi.md#coursesEventsParticipationsCreate) | **POST** /courses/{course_pk}/events/{event_pk}/participations/ | 
[**coursesEventsParticipationsList**](CoursesApi.md#coursesEventsParticipationsList) | **GET** /courses/{course_pk}/events/{event_pk}/participations/ | 
[**coursesEventsParticipationsPartialUpdate**](CoursesApi.md#coursesEventsParticipationsPartialUpdate) | **PATCH** /courses/{course_pk}/events/{event_pk}/participations/{id}/ | 
[**coursesEventsParticipationsRead**](CoursesApi.md#coursesEventsParticipationsRead) | **GET** /courses/{course_pk}/events/{event_pk}/participations/{id}/ | 
[**coursesEventsParticipationsSlotsList**](CoursesApi.md#coursesEventsParticipationsSlotsList) | **GET** /courses/{course_pk}/events/{event_pk}/participations/{participation_pk}/slots/ | 
[**coursesEventsParticipationsSlotsPartialUpdate**](CoursesApi.md#coursesEventsParticipationsSlotsPartialUpdate) | **PATCH** /courses/{course_pk}/events/{event_pk}/participations/{participation_pk}/slots/{id}/ | 
[**coursesEventsParticipationsSlotsRead**](CoursesApi.md#coursesEventsParticipationsSlotsRead) | **GET** /courses/{course_pk}/events/{event_pk}/participations/{participation_pk}/slots/{id}/ | 
[**coursesEventsParticipationsSlotsUpdate**](CoursesApi.md#coursesEventsParticipationsSlotsUpdate) | **PUT** /courses/{course_pk}/events/{event_pk}/participations/{participation_pk}/slots/{id}/ | 
[**coursesEventsParticipationsUpdate**](CoursesApi.md#coursesEventsParticipationsUpdate) | **PUT** /courses/{course_pk}/events/{event_pk}/participations/{id}/ | 
[**coursesEventsRead**](CoursesApi.md#coursesEventsRead) | **GET** /courses/{course_pk}/events/{id}/ | 
[**coursesEventsUpdate**](CoursesApi.md#coursesEventsUpdate) | **PUT** /courses/{course_pk}/events/{id}/ | 
[**coursesExercisesChoicesCreate**](CoursesApi.md#coursesExercisesChoicesCreate) | **POST** /courses/{course_pk}/exercises/{exercise_pk}/choices/ | 
[**coursesExercisesChoicesDelete**](CoursesApi.md#coursesExercisesChoicesDelete) | **DELETE** /courses/{course_pk}/exercises/{exercise_pk}/choices/{id}/ | 
[**coursesExercisesChoicesList**](CoursesApi.md#coursesExercisesChoicesList) | **GET** /courses/{course_pk}/exercises/{exercise_pk}/choices/ | 
[**coursesExercisesChoicesPartialUpdate**](CoursesApi.md#coursesExercisesChoicesPartialUpdate) | **PATCH** /courses/{course_pk}/exercises/{exercise_pk}/choices/{id}/ | 
[**coursesExercisesChoicesRead**](CoursesApi.md#coursesExercisesChoicesRead) | **GET** /courses/{course_pk}/exercises/{exercise_pk}/choices/{id}/ | 
[**coursesExercisesChoicesUpdate**](CoursesApi.md#coursesExercisesChoicesUpdate) | **PUT** /courses/{course_pk}/exercises/{exercise_pk}/choices/{id}/ | 
[**coursesExercisesCreate**](CoursesApi.md#coursesExercisesCreate) | **POST** /courses/{course_pk}/exercises/ | 
[**coursesExercisesDelete**](CoursesApi.md#coursesExercisesDelete) | **DELETE** /courses/{course_pk}/exercises/{id}/ | 
[**coursesExercisesList**](CoursesApi.md#coursesExercisesList) | **GET** /courses/{course_pk}/exercises/ | 
[**coursesExercisesPartialUpdate**](CoursesApi.md#coursesExercisesPartialUpdate) | **PATCH** /courses/{course_pk}/exercises/{id}/ | 
[**coursesExercisesRead**](CoursesApi.md#coursesExercisesRead) | **GET** /courses/{course_pk}/exercises/{id}/ | 
[**coursesExercisesSubExercisesCreate**](CoursesApi.md#coursesExercisesSubExercisesCreate) | **POST** /courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/ | 
[**coursesExercisesSubExercisesDelete**](CoursesApi.md#coursesExercisesSubExercisesDelete) | **DELETE** /courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/{id}/ | 
[**coursesExercisesSubExercisesList**](CoursesApi.md#coursesExercisesSubExercisesList) | **GET** /courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/ | 
[**coursesExercisesSubExercisesPartialUpdate**](CoursesApi.md#coursesExercisesSubExercisesPartialUpdate) | **PATCH** /courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/{id}/ | 
[**coursesExercisesSubExercisesRead**](CoursesApi.md#coursesExercisesSubExercisesRead) | **GET** /courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/{id}/ | 
[**coursesExercisesSubExercisesUpdate**](CoursesApi.md#coursesExercisesSubExercisesUpdate) | **PUT** /courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/{id}/ | 
[**coursesExercisesUpdate**](CoursesApi.md#coursesExercisesUpdate) | **PUT** /courses/{course_pk}/exercises/{id}/ | 
[**coursesList**](CoursesApi.md#coursesList) | **GET** /courses/ | 
[**coursesPartialUpdate**](CoursesApi.md#coursesPartialUpdate) | **PATCH** /courses/{id}/ | 
[**coursesRead**](CoursesApi.md#coursesRead) | **GET** /courses/{id}/ | 
[**coursesTemplatesCreate**](CoursesApi.md#coursesTemplatesCreate) | **POST** /courses/{course_pk}/templates/ | 
[**coursesTemplatesDelete**](CoursesApi.md#coursesTemplatesDelete) | **DELETE** /courses/{course_pk}/templates/{id}/ | 
[**coursesTemplatesList**](CoursesApi.md#coursesTemplatesList) | **GET** /courses/{course_pk}/templates/ | 
[**coursesTemplatesPartialUpdate**](CoursesApi.md#coursesTemplatesPartialUpdate) | **PATCH** /courses/{course_pk}/templates/{id}/ | 
[**coursesTemplatesRead**](CoursesApi.md#coursesTemplatesRead) | **GET** /courses/{course_pk}/templates/{id}/ | 
[**coursesTemplatesUpdate**](CoursesApi.md#coursesTemplatesUpdate) | **PUT** /courses/{course_pk}/templates/{id}/ | 
[**coursesUpdate**](CoursesApi.md#coursesUpdate) | **PUT** /courses/{id}/ | 


<a name="coursesCreate"></a>
# **coursesCreate**
> Course coursesCreate(data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var data = new SnippetsApi.Course(); // Course | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesCreate(data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **data** | [**Course**](Course.md)|  | 

### Return type

[**Course**](Course.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesDelete"></a>
# **coursesDelete**
> coursesDelete(id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var id = 56; // Number | A unique integer value identifying this course.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesDelete(id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **Number**| A unique integer value identifying this course. | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsCreate"></a>
# **coursesEventsCreate**
> Event coursesEventsCreate(coursePk, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var data = new SnippetsApi.Event(); // Event | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesEventsCreate(coursePk, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **data** | [**Event**](Event.md)|  | 

### Return type

[**Event**](Event.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsDelete"></a>
# **coursesEventsDelete**
> coursesEventsDelete(coursePk, id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesEventsDelete(coursePk, id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event. | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsList"></a>
# **coursesEventsList**
> [Event] coursesEventsList(coursePk, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesEventsList(coursePk, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 

### Return type

[**[Event]**](Event.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsPartialUpdate"></a>
# **coursesEventsPartialUpdate**
> Event coursesEventsPartialUpdate(coursePk, id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event.

var data = new SnippetsApi.Event(); // Event | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesEventsPartialUpdate(coursePk, id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event. | 
 **data** | [**Event**](Event.md)|  | 

### Return type

[**Event**](Event.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsParticipationsCreate"></a>
# **coursesEventsParticipationsCreate**
> coursesEventsParticipationsCreate(coursePk, eventPk)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var eventPk = "eventPk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesEventsParticipationsCreate(coursePk, eventPk, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **eventPk** | **String**|  | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsParticipationsList"></a>
# **coursesEventsParticipationsList**
> coursesEventsParticipationsList(coursePk, eventPk)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var eventPk = "eventPk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesEventsParticipationsList(coursePk, eventPk, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **eventPk** | **String**|  | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsParticipationsPartialUpdate"></a>
# **coursesEventsParticipationsPartialUpdate**
> coursesEventsParticipationsPartialUpdate(coursePk, eventPk, id)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var eventPk = "eventPk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event participation.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesEventsParticipationsPartialUpdate(coursePk, eventPk, id, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **eventPk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event participation. | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsParticipationsRead"></a>
# **coursesEventsParticipationsRead**
> coursesEventsParticipationsRead(coursePk, eventPk, id)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var eventPk = "eventPk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event participation.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesEventsParticipationsRead(coursePk, eventPk, id, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **eventPk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event participation. | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsParticipationsSlotsList"></a>
# **coursesEventsParticipationsSlotsList**
> coursesEventsParticipationsSlotsList(coursePk, eventPk, participationPk)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var eventPk = "eventPk_example"; // String | 

var participationPk = "participationPk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesEventsParticipationsSlotsList(coursePk, eventPk, participationPk, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **eventPk** | **String**|  | 
 **participationPk** | **String**|  | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsParticipationsSlotsPartialUpdate"></a>
# **coursesEventsParticipationsSlotsPartialUpdate**
> coursesEventsParticipationsSlotsPartialUpdate(coursePk, eventPk, id, participationPk)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var eventPk = "eventPk_example"; // String | 

var id = "id_example"; // String | 

var participationPk = "participationPk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesEventsParticipationsSlotsPartialUpdate(coursePk, eventPk, id, participationPk, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **eventPk** | **String**|  | 
 **id** | **String**|  | 
 **participationPk** | **String**|  | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsParticipationsSlotsRead"></a>
# **coursesEventsParticipationsSlotsRead**
> coursesEventsParticipationsSlotsRead(coursePk, eventPk, id, participationPk)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var eventPk = "eventPk_example"; // String | 

var id = "id_example"; // String | 

var participationPk = "participationPk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesEventsParticipationsSlotsRead(coursePk, eventPk, id, participationPk, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **eventPk** | **String**|  | 
 **id** | **String**|  | 
 **participationPk** | **String**|  | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsParticipationsSlotsUpdate"></a>
# **coursesEventsParticipationsSlotsUpdate**
> coursesEventsParticipationsSlotsUpdate(coursePk, eventPk, id, participationPk)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var eventPk = "eventPk_example"; // String | 

var id = "id_example"; // String | 

var participationPk = "participationPk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesEventsParticipationsSlotsUpdate(coursePk, eventPk, id, participationPk, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **eventPk** | **String**|  | 
 **id** | **String**|  | 
 **participationPk** | **String**|  | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsParticipationsUpdate"></a>
# **coursesEventsParticipationsUpdate**
> coursesEventsParticipationsUpdate(coursePk, eventPk, id)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var eventPk = "eventPk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event participation.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesEventsParticipationsUpdate(coursePk, eventPk, id, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **eventPk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event participation. | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsRead"></a>
# **coursesEventsRead**
> Event coursesEventsRead(coursePk, id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesEventsRead(coursePk, id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event. | 

### Return type

[**Event**](Event.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesEventsUpdate"></a>
# **coursesEventsUpdate**
> Event coursesEventsUpdate(coursePk, id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event.

var data = new SnippetsApi.Event(); // Event | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesEventsUpdate(coursePk, id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event. | 
 **data** | [**Event**](Event.md)|  | 

### Return type

[**Event**](Event.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesChoicesCreate"></a>
# **coursesExercisesChoicesCreate**
> ExerciseChoice coursesExercisesChoicesCreate(coursePk, exercisePk, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 

var data = new SnippetsApi.ExerciseChoice(); // ExerciseChoice | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesChoicesCreate(coursePk, exercisePk, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 
 **data** | [**ExerciseChoice**](ExerciseChoice.md)|  | 

### Return type

[**ExerciseChoice**](ExerciseChoice.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesChoicesDelete"></a>
# **coursesExercisesChoicesDelete**
> coursesExercisesChoicesDelete(coursePk, exercisePk, id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise choice.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesExercisesChoicesDelete(coursePk, exercisePk, id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise choice. | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesChoicesList"></a>
# **coursesExercisesChoicesList**
> [ExerciseChoice] coursesExercisesChoicesList(coursePk, exercisePk, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesChoicesList(coursePk, exercisePk, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 

### Return type

[**[ExerciseChoice]**](ExerciseChoice.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesChoicesPartialUpdate"></a>
# **coursesExercisesChoicesPartialUpdate**
> ExerciseChoice coursesExercisesChoicesPartialUpdate(coursePk, exercisePk, id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise choice.

var data = new SnippetsApi.ExerciseChoice(); // ExerciseChoice | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesChoicesPartialUpdate(coursePk, exercisePk, id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise choice. | 
 **data** | [**ExerciseChoice**](ExerciseChoice.md)|  | 

### Return type

[**ExerciseChoice**](ExerciseChoice.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesChoicesRead"></a>
# **coursesExercisesChoicesRead**
> ExerciseChoice coursesExercisesChoicesRead(coursePk, exercisePk, id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise choice.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesChoicesRead(coursePk, exercisePk, id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise choice. | 

### Return type

[**ExerciseChoice**](ExerciseChoice.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesChoicesUpdate"></a>
# **coursesExercisesChoicesUpdate**
> ExerciseChoice coursesExercisesChoicesUpdate(coursePk, exercisePk, id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise choice.

var data = new SnippetsApi.ExerciseChoice(); // ExerciseChoice | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesChoicesUpdate(coursePk, exercisePk, id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise choice. | 
 **data** | [**ExerciseChoice**](ExerciseChoice.md)|  | 

### Return type

[**ExerciseChoice**](ExerciseChoice.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesCreate"></a>
# **coursesExercisesCreate**
> Exercise coursesExercisesCreate(coursePk, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var data = new SnippetsApi.Exercise(); // Exercise | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesCreate(coursePk, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **data** | [**Exercise**](Exercise.md)|  | 

### Return type

[**Exercise**](Exercise.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesDelete"></a>
# **coursesExercisesDelete**
> coursesExercisesDelete(coursePk, id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesExercisesDelete(coursePk, id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise. | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesList"></a>
# **coursesExercisesList**
> [Exercise] coursesExercisesList(coursePk, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesList(coursePk, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 

### Return type

[**[Exercise]**](Exercise.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesPartialUpdate"></a>
# **coursesExercisesPartialUpdate**
> Exercise coursesExercisesPartialUpdate(coursePk, id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise.

var data = new SnippetsApi.Exercise(); // Exercise | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesPartialUpdate(coursePk, id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise. | 
 **data** | [**Exercise**](Exercise.md)|  | 

### Return type

[**Exercise**](Exercise.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesRead"></a>
# **coursesExercisesRead**
> Exercise coursesExercisesRead(coursePk, id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesRead(coursePk, id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise. | 

### Return type

[**Exercise**](Exercise.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesSubExercisesCreate"></a>
# **coursesExercisesSubExercisesCreate**
> Exercise coursesExercisesSubExercisesCreate(coursePk, exercisePk, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 

var data = new SnippetsApi.Exercise(); // Exercise | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesSubExercisesCreate(coursePk, exercisePk, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 
 **data** | [**Exercise**](Exercise.md)|  | 

### Return type

[**Exercise**](Exercise.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesSubExercisesDelete"></a>
# **coursesExercisesSubExercisesDelete**
> coursesExercisesSubExercisesDelete(coursePk, exercisePk, id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesExercisesSubExercisesDelete(coursePk, exercisePk, id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise. | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesSubExercisesList"></a>
# **coursesExercisesSubExercisesList**
> [Exercise] coursesExercisesSubExercisesList(coursePk, exercisePk, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesSubExercisesList(coursePk, exercisePk, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 

### Return type

[**[Exercise]**](Exercise.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesSubExercisesPartialUpdate"></a>
# **coursesExercisesSubExercisesPartialUpdate**
> Exercise coursesExercisesSubExercisesPartialUpdate(coursePk, exercisePk, id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise.

var data = new SnippetsApi.Exercise(); // Exercise | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesSubExercisesPartialUpdate(coursePk, exercisePk, id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise. | 
 **data** | [**Exercise**](Exercise.md)|  | 

### Return type

[**Exercise**](Exercise.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesSubExercisesRead"></a>
# **coursesExercisesSubExercisesRead**
> Exercise coursesExercisesSubExercisesRead(coursePk, exercisePk, id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesSubExercisesRead(coursePk, exercisePk, id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise. | 

### Return type

[**Exercise**](Exercise.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesSubExercisesUpdate"></a>
# **coursesExercisesSubExercisesUpdate**
> Exercise coursesExercisesSubExercisesUpdate(coursePk, exercisePk, id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var exercisePk = "exercisePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise.

var data = new SnippetsApi.Exercise(); // Exercise | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesSubExercisesUpdate(coursePk, exercisePk, id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **exercisePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise. | 
 **data** | [**Exercise**](Exercise.md)|  | 

### Return type

[**Exercise**](Exercise.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesExercisesUpdate"></a>
# **coursesExercisesUpdate**
> Exercise coursesExercisesUpdate(coursePk, id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this exercise.

var data = new SnippetsApi.Exercise(); // Exercise | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesExercisesUpdate(coursePk, id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this exercise. | 
 **data** | [**Exercise**](Exercise.md)|  | 

### Return type

[**Exercise**](Exercise.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesList"></a>
# **coursesList**
> [Course] coursesList()





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesList(callback);
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**[Course]**](Course.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesPartialUpdate"></a>
# **coursesPartialUpdate**
> Course coursesPartialUpdate(id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var id = 56; // Number | A unique integer value identifying this course.

var data = new SnippetsApi.Course(); // Course | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesPartialUpdate(id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **Number**| A unique integer value identifying this course. | 
 **data** | [**Course**](Course.md)|  | 

### Return type

[**Course**](Course.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesRead"></a>
# **coursesRead**
> Course coursesRead(id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var id = 56; // Number | A unique integer value identifying this course.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesRead(id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **Number**| A unique integer value identifying this course. | 

### Return type

[**Course**](Course.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesTemplatesCreate"></a>
# **coursesTemplatesCreate**
> EventTemplate coursesTemplatesCreate(coursePk, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var data = new SnippetsApi.EventTemplate(); // EventTemplate | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesTemplatesCreate(coursePk, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **data** | [**EventTemplate**](EventTemplate.md)|  | 

### Return type

[**EventTemplate**](EventTemplate.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesTemplatesDelete"></a>
# **coursesTemplatesDelete**
> coursesTemplatesDelete(coursePk, id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event template.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.coursesTemplatesDelete(coursePk, id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event template. | 

### Return type

null (empty response body)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesTemplatesList"></a>
# **coursesTemplatesList**
> [EventTemplate] coursesTemplatesList(coursePk, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesTemplatesList(coursePk, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 

### Return type

[**[EventTemplate]**](EventTemplate.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesTemplatesPartialUpdate"></a>
# **coursesTemplatesPartialUpdate**
> EventTemplate coursesTemplatesPartialUpdate(coursePk, id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event template.

var data = new SnippetsApi.EventTemplate(); // EventTemplate | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesTemplatesPartialUpdate(coursePk, id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event template. | 
 **data** | [**EventTemplate**](EventTemplate.md)|  | 

### Return type

[**EventTemplate**](EventTemplate.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesTemplatesRead"></a>
# **coursesTemplatesRead**
> EventTemplate coursesTemplatesRead(coursePk, id, )





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event template.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesTemplatesRead(coursePk, id, , callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event template. | 

### Return type

[**EventTemplate**](EventTemplate.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesTemplatesUpdate"></a>
# **coursesTemplatesUpdate**
> EventTemplate coursesTemplatesUpdate(coursePk, id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var coursePk = "coursePk_example"; // String | 

var id = 56; // Number | A unique integer value identifying this event template.

var data = new SnippetsApi.EventTemplate(); // EventTemplate | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesTemplatesUpdate(coursePk, id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **coursePk** | **String**|  | 
 **id** | **Number**| A unique integer value identifying this event template. | 
 **data** | [**EventTemplate**](EventTemplate.md)|  | 

### Return type

[**EventTemplate**](EventTemplate.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a name="coursesUpdate"></a>
# **coursesUpdate**
> Course coursesUpdate(id, data)





### Example
```javascript
var SnippetsApi = require('snippets_api');
var defaultClient = SnippetsApi.ApiClient.instance;

// Configure HTTP basic authorization: Basic
var Basic = defaultClient.authentications['Basic'];
Basic.username = 'YOUR USERNAME';
Basic.password = 'YOUR PASSWORD';

var apiInstance = new SnippetsApi.CoursesApi();

var id = 56; // Number | A unique integer value identifying this course.

var data = new SnippetsApi.Course(); // Course | 


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.coursesUpdate(id, data, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **Number**| A unique integer value identifying this course. | 
 **data** | [**Course**](Course.md)|  | 

### Return type

[**Course**](Course.md)

### Authorization

[Basic](../README.md#Basic)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

