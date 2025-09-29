angular.module('digitalprint.services')
    .factory('DynamicCssService', function($rootScope, $document, $config) {

        var DynamicCssService = {};

        DynamicCssService.loadDomainCSS = function(domainID, companyID) {
            var staticUrl = $config.STATIC_URL || 'http://localtest.me/static/';
            var cssLink = $document[0].createElement('link');

            cssLink.rel = 'stylesheet';
            cssLink.type = 'text/css';
            cssLink.href = staticUrl + companyID + '/styles/' + domainID + '/main.css';

            // Remove any existing domain-specific CSS
            var existingLink = $document[0].querySelector('#dynamic-css');
            if (existingLink) {
                existingLink.parentNode.removeChild(existingLink);
            }

            // Set an ID for easier management
            cssLink.id = 'dynamic-css';

            // Append the new CSS file to the head
            $document[0].getElementsByTagName('head')[0].appendChild(cssLink);
        };

        return DynamicCssService;
    });
