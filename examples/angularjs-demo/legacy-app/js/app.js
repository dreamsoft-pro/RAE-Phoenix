/**
 * AngularJS 1.3 TODO Application
 * Main application module and routing configuration
 *
 * This is a legacy AngularJS 1.3 application that demonstrates
 * patterns commonly found in real-world apps:
 * - $routeProvider routing
 * - Controller-as syntax
 * - Dependency injection
 * - Services
 * - Filters
 * - Directives
 */

(function() {
    'use strict';

    angular.module('todoApp', ['ngRoute'])
        .config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider) {
            $routeProvider
                .when('/todos', {
                    templateUrl: 'views/todo-list.html',
                    controller: 'TodoController',
                    controllerAs: 'vm'
                })
                .when('/todos/active', {
                    templateUrl: 'views/todo-list.html',
                    controller: 'TodoController',
                    controllerAs: 'vm',
                    resolve: {
                        filter: function() {
                            return 'active';
                        }
                    }
                })
                .when('/todos/completed', {
                    templateUrl: 'views/todo-list.html',
                    controller: 'TodoController',
                    controllerAs: 'vm',
                    resolve: {
                        filter: function() {
                            return 'completed';
                        }
                    }
                })
                .when('/todos/:id', {
                    templateUrl: 'views/todo-detail.html',
                    controller: 'TodoDetailController',
                    controllerAs: 'vm'
                })
                .otherwise({
                    redirectTo: '/todos'
                });

            // Disable HTML5 mode for simplicity
            $locationProvider.html5Mode(false);
        }])
        .run(['$rootScope', function($rootScope) {
            // Global app state
            $rootScope.appName = 'TODO App';
            $rootScope.version = '1.0.0';

            // Route change listeners
            $rootScope.$on('$routeChangeStart', function(event, next, current) {
                console.log('Route changing from', current, 'to', next);
            });

            $rootScope.$on('$routeChangeSuccess', function(event, current, previous) {
                console.log('Route changed successfully');
            });
        }]);
})();
