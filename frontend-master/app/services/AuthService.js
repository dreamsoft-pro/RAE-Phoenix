angular.module('myApp').service('AuthService', function($http) {
    this.login = function(creds) {
        return $http.post('/api/auth/login', creds);
    };
});
