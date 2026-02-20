/**
 * TodoFilters - Custom filters for TODO app
 * Demonstrates AngularJS filter patterns
 */

(function() {
    'use strict';

    angular.module('todoApp')
        .filter('capitalize', capitalizeFilter)
        .filter('priorityLabel', priorityLabelFilter)
        .filter('dateFormat', dateFormatFilter)
        .filter('todoStatus', todoStatusFilter);

    /**
     * Capitalize first letter of string
     */
    function capitalizeFilter() {
        return function(input) {
            if (!input) return '';
            return input.charAt(0).toUpperCase() + input.slice(1);
        };
    }

    /**
     * Convert priority to display label
     */
    function priorityLabelFilter() {
        return function(priority) {
            var labels = {
                'high': '🔴 High',
                'medium': '🟡 Medium',
                'low': '🟢 Low'
            };
            return labels[priority] || priority;
        };
    }

    /**
     * Format date string
     */
    function dateFormatFilter() {
        return function(dateString) {
            if (!dateString) return '';
            var date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        };
    }

    /**
     * Get status label for todo
     */
    function todoStatusFilter() {
        return function(todo) {
            if (!todo) return '';
            return todo.completed ? '✅ Completed' : '⏳ Active';
        };
    }
})();
