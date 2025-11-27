/**
 * TodoService - Handles TODO data operations
 * Demonstrates AngularJS service patterns with $http
 */

(function() {
    'use strict';

    angular.module('todoApp')
        .factory('TodoService', ['$http', '$q', '$timeout', function($http, $q, $timeout) {
            // Simulated backend data
            var todos = [
                { id: 1, title: 'Learn AngularJS', completed: true, priority: 'high', createdAt: '2025-01-15' },
                { id: 2, title: 'Build TODO app', completed: true, priority: 'high', createdAt: '2025-01-16' },
                { id: 3, title: 'Migrate to Next.js', completed: false, priority: 'high', createdAt: '2025-01-20' },
                { id: 4, title: 'Deploy to production', completed: false, priority: 'medium', createdAt: '2025-01-22' }
            ];

            var nextId = 5;

            /**
             * Get all todos
             * @returns {Promise} Promise resolving to array of todos
             */
            function getAllTodos() {
                var deferred = $q.defer();

                // Simulate async API call
                $timeout(function() {
                    deferred.resolve(angular.copy(todos));
                }, 100);

                return deferred.promise;
            }

            /**
             * Get todo by ID
             * @param {number} id - Todo ID
             * @returns {Promise} Promise resolving to todo object
             */
            function getTodoById(id) {
                var deferred = $q.defer();

                $timeout(function() {
                    var todo = todos.find(function(t) { return t.id === parseInt(id); });
                    if (todo) {
                        deferred.resolve(angular.copy(todo));
                    } else {
                        deferred.reject('Todo not found');
                    }
                }, 50);

                return deferred.promise;
            }

            /**
             * Create new todo
             * @param {Object} todoData - New todo data
             * @returns {Promise} Promise resolving to created todo
             */
            function createTodo(todoData) {
                var deferred = $q.defer();

                $timeout(function() {
                    var newTodo = {
                        id: nextId++,
                        title: todoData.title,
                        completed: false,
                        priority: todoData.priority || 'medium',
                        createdAt: new Date().toISOString().split('T')[0]
                    };
                    todos.push(newTodo);
                    deferred.resolve(angular.copy(newTodo));
                }, 100);

                return deferred.promise;
            }

            /**
             * Update todo
             * @param {number} id - Todo ID
             * @param {Object} updates - Updated fields
             * @returns {Promise} Promise resolving to updated todo
             */
            function updateTodo(id, updates) {
                var deferred = $q.defer();

                $timeout(function() {
                    var todo = todos.find(function(t) { return t.id === id; });
                    if (todo) {
                        angular.extend(todo, updates);
                        deferred.resolve(angular.copy(todo));
                    } else {
                        deferred.reject('Todo not found');
                    }
                }, 100);

                return deferred.promise;
            }

            /**
             * Delete todo
             * @param {number} id - Todo ID
             * @returns {Promise} Promise resolving on success
             */
            function deleteTodo(id) {
                var deferred = $q.defer();

                $timeout(function() {
                    var index = todos.findIndex(function(t) { return t.id === id; });
                    if (index !== -1) {
                        todos.splice(index, 1);
                        deferred.resolve();
                    } else {
                        deferred.reject('Todo not found');
                    }
                }, 100);

                return deferred.promise;
            }

            /**
             * Get statistics about todos
             * @returns {Promise} Promise resolving to stats object
             */
            function getStats() {
                var deferred = $q.defer();

                $timeout(function() {
                    var stats = {
                        total: todos.length,
                        completed: todos.filter(function(t) { return t.completed; }).length,
                        active: todos.filter(function(t) { return !t.completed; }).length,
                        highPriority: todos.filter(function(t) { return t.priority === 'high'; }).length
                    };
                    deferred.resolve(stats);
                }, 50);

                return deferred.promise;
            }

            // Public API
            return {
                getAllTodos: getAllTodos,
                getTodoById: getTodoById,
                createTodo: createTodo,
                updateTodo: updateTodo,
                deleteTodo: deleteTodo,
                getStats: getStats
            };
        }]);
})();
