DFL_ALL_TESTCASES_JS_TEMPLATE = """
const {{ ID_1 }} = []; // array containing results objects
{{ USER_CODE }}
let {{ ID_2 }} = 0 // test index counter
{% for test in TESTCASES %}
var {{ ID_3 }} = {id: {{ test.id }}} // object containing results for this testcase
try {
    {{ test.code }}
    {{ ID_3 }}.passed = true // no exception thrown by test; test passed
} catch(e) {
    {{ ID_3 }}.passed = false
    if(e instanceof {{ ID_4 }}) { // assertion error
         {{ ID_3 }}.error = {{ ID_4 }}(e)
    } else {
        {{ ID_3 }}.error = {{ ID_5 }}(e)
    }
} finally {
    {{ ID_1 }}[{{ ID_2 }}++] = {{ ID_3 }}
}
{% endfor %}
{{ ID_1 }} // evaluate to the array containing results
"""
