/**
 * TodoController - Main controller for TODO list
 * Demonstrates common AngularJS patterns:
 * - Controller-as syntax
 * - Dependency injection
 * - $scope usage
 * - Service integration
 * - $watch for reactive updates
 */

(function() {
    'use strict';

    angular.module('todoApp')
        .controller('TodoController', TodoController)
        .controller('TodoDetailController', TodoDetailController);

    TodoController.$inject = ['$scope', '$rootScope', '$location', 'TodoService', 'filter'];

    function TodoController($scope, $rootScope, $location, TodoService, filter) {
        var vm = this;

        // View state
        vm.todos = [];
        vm.newTodo = {
            title: '',
            priority: 'medium'
        };
        vm.loading = true;
        vm.error = null;
        vm.filterMode = filter || 'all';
        vm.stats = {};

        // Methods
        vm.loadTodos = loadTodos;
        vm.createTodo = createTodo;
        vm.toggleComplete = toggleComplete;
        vm.deleteTodo = deleteTodo;
        vm.editTodo = editTodo;
        vm.viewTodoDetail = viewTodoDetail;
        vm.clearCompleted = clearCompleted;

        // Initialize
        activate();

        ///////////////

        function activate() {
            loadTodos();
            loadStats();

            // Watch for changes in todos to update stats
            $scope.$watch(function() {
                return vm.todos.length;
            }, function(newVal, oldVal) {
                if (newVal !== oldVal) {
                    loadStats();
                }
            });

            // Listen for global events
            $rootScope.$on('todo:created', function(event, todo) {
                console.log('Todo created event received:', todo);
            });

            $rootScope.$on('todo:deleted', function(event, todoId) {
                console.log('Todo deleted event received:', todoId);
            });
        }

        function loadTodos() {
            vm.loading = true;
            vm.error = null;

            TodoService.getAllTodos()
                .then(function(todos) {
                    vm.todos = todos;
                    applyFilter();
                    vm.loading = false;
                })
                .catch(function(error) {
                    vm.error = 'Failed to load todos: ' + error;
                    vm.loading = false;
                });
        }

        function loadStats() {
            TodoService.getStats()
                .then(function(stats) {
                    vm.stats = stats;
                });
        }

        function applyFilter() {
            if (vm.filterMode === 'active') {
                vm.filteredTodos = vm.todos.filter(function(todo) {
                    return !todo.completed;
                });
            } else if (vm.filterMode === 'completed') {
                vm.filteredTodos = vm.todos.filter(function(todo) {
                    return todo.completed;
                });
            } else {
                vm.filteredTodos = vm.todos;
            }
        }

        function createTodo() {
            if (!vm.newTodo.title || vm.newTodo.title.trim() === '') {
                return;
            }

            TodoService.createTodo(vm.newTodo)
                .then(function(todo) {
                    vm.todos.push(todo);
                    vm.newTodo = { title: '', priority: 'medium' };
                    applyFilter();
                    $rootScope.$broadcast('todo:created', todo);
                })
                .catch(function(error) {
                    vm.error = 'Failed to create todo: ' + error;
                });
        }

        function toggleComplete(todo) {
            var updates = { completed: !todo.completed };

            TodoService.updateTodo(todo.id, updates)
                .then(function(updatedTodo) {
                    angular.extend(todo, updatedTodo);
                    applyFilter();
                    loadStats();
                })
                .catch(function(error) {
                    vm.error = 'Failed to update todo: ' + error;
                });
        }

        function deleteTodo(todo) {
            if (!confirm('Are you sure you want to delete this todo?')) {
                return;
            }

            TodoService.deleteTodo(todo.id)
                .then(function() {
                    var index = vm.todos.indexOf(todo);
                    if (index !== -1) {
                        vm.todos.splice(index, 1);
                    }
                    applyFilter();
                    $rootScope.$broadcast('todo:deleted', todo.id);
                })
                .catch(function(error) {
                    vm.error = 'Failed to delete todo: ' + error;
                });
        }

        function editTodo(todo) {
            todo.editing = true;
            todo.originalTitle = todo.title;
        }

        function viewTodoDetail(todo) {
            $location.path('/todos/' + todo.id);
        }

        function clearCompleted() {
            var completedTodos = vm.todos.filter(function(todo) {
                return todo.completed;
            });

            var promises = completedTodos.map(function(todo) {
                return TodoService.deleteTodo(todo.id);
            });

            Promise.all(promises)
                .then(function() {
                    loadTodos();
                })
                .catch(function(error) {
                    vm.error = 'Failed to clear completed todos: ' + error;
                });
        }
    }

    TodoDetailController.$inject = ['$scope', '$routeParams', '$location', 'TodoService'];

    function TodoDetailController($scope, $routeParams, $location, TodoService) {
        var vm = this;

        vm.todo = null;
        vm.loading = true;
        vm.error = null;

        vm.goBack = goBack;
        vm.toggleComplete = toggleComplete;
        vm.deleteTodo = deleteTodo;

        activate();

        ///////////////

        function activate() {
            var todoId = parseInt($routeParams.id);

            TodoService.getTodoById(todoId)
                .then(function(todo) {
                    vm.todo = todo;
                    vm.loading = false;
                })
                .catch(function(error) {
                    vm.error = 'Todo not found';
                    vm.loading = false;
                });
        }

        function goBack() {
            $location.path('/todos');
        }

        function toggleComplete() {
            var updates = { completed: !vm.todo.completed };

            TodoService.updateTodo(vm.todo.id, updates)
                .then(function(updatedTodo) {
                    angular.extend(vm.todo, updatedTodo);
                })
                .catch(function(error) {
                    vm.error = 'Failed to update todo: ' + error;
                });
        }

        function deleteTodo() {
            if (!confirm('Are you sure you want to delete this todo?')) {
                return;
            }

            TodoService.deleteTodo(vm.todo.id)
                .then(function() {
                    goBack();
                })
                .catch(function(error) {
                    vm.error = 'Failed to delete todo: ' + error;
                });
        }
    }
})();
