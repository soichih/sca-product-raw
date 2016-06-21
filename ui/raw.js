(function() {
    'use strict';

    //https://github.com/danialfarid/ng-file-upload
    var service = angular.module('sca-product-raw', [ ]);
    service.directive('scaProductRaw', ['toaster', '$http', '$timeout', 'scaTask', 'appconf',
    function(toaster, $http, $timeout, scaTask, appconf) {
        return {
            restrict: 'E',
            scope: {
                taskid: '=',
                path: '=?', //if empty, it will be set to instantce_id / task_id (relative to task dir)
            }, 
            templateUrl: 'bower_components/sca-product-raw/ui/raw.html',
            link: function($scope, element) {
                $scope.jwt = localStorage.getItem(appconf.jwt_id);
                $scope.appconf = appconf; //used by template
                if(!$scope.path) $scope.path = "";

                var file_timeout;
                $scope.t = scaTask.get($scope.taskid);
                $scope.t._promise.then(function() {
                    $scope.taskdir = $scope.t.instance_id+"/"+$scope.t._id;

                    //reload files if resource_id is set
                    if($scope.t.resource_id) {
                        $scope.loading = true;
                        //$scope.path = $scope.path || $scope.t.instance_id+"/"+$scope.t._id;
                        //$scope.path = $scope.t.instance_id+"/"+$scope.t._id;
                        $http.get(appconf.sca_api+"/resource/ls/"+$scope.t.resource_id, {
                            //timeout: 3000, //server side should handle this (with good explanation)
                            params: {
                                path: $scope.taskdir+"/"+$scope.path,
                            }
                        })
                        .then(function(res) {
                            $scope.loading = false;
                            $scope.files = res.data.files;
                            $scope.files.forEach(function(file) {
                                file.path = $scope.path+"/"+file.filename;
                            });
                        }, function(res) {
                            $scope.loading = false;
                            if(res.data && res.data.message) toaster.error(res.data.message);
                            else toaster.error(res.statusText);
                        });
                    } else {
                        console.log("resource_id not loaded yet..");
                    }
                });

                $scope.$on("$destroy", function(event) {
                    if(file_timeout) $timeout.cancel(file_timeout);
                });
            }
        };
    }]);

    //can't quite do the slidedown animation through pure angular/css.. borrowing slideDown from jQuery..
    service.animation('.slide-down', ['$animateCss', function($animateCss) {
        return {
            enter: function(elem, done) {
                $(elem).hide().slideDown("normal", done);
            },
            leave: function(elem, done) {
                $(elem).slideUp("normal", done);
            }
        };
    }]);

    service.filter('bytes', function() {
        return function(bytes, precision) {
            if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
            if (typeof precision === 'undefined') precision = 1;
            var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'],
                number = Math.floor(Math.log(bytes) / Math.log(1024));
            return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +  ' ' + units[number];
        }
    });

    service.filter('encodeURI', function() {
      return window.encodeURIComponent;
    });
        
    //end of IIFE (immediately-invoked function expression)
})();


