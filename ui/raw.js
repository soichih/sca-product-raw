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
            }
        };
    }]);

    service.component('scaProductRawDir', {
        //transclude: true,
        bindings: {
            taskid: '=',
            indent: '=',
            path: '=?', //if empty, it will be set to instantce_id / task_id (relative to task dir)
        },
        templateUrl: 'bower_components/sca-product-raw/ui/dir.html',
        controller: function($scope, appconf, $http, toaster, scaTask) {
            var $ctrl = this;
            var jwt = localStorage.getItem(appconf.jwt_id);
            this.indent_child = this.indent+1;
            if(!this.path) this.path = "";

            this.getNumber = function(num) { return new Array(num); };

            //start by loading task
            var t = scaTask.get(this.taskid);
            t._promise.then(function() {
                $ctrl.taskdir = t.instance_id+"/"+t._id;
                if(!t.resource_id) {
                    console.error("sca-product-raw initialized on task with no resource_id");
                    return;
                }

                $ctrl.loading = true;
                console.log("loading from resource:"+t.resource_id+" path:"+$ctrl.taskdir+"/"+$ctrl.path);
                $http.get(appconf.sca_api+"/resource/ls/"+t.resource_id, {
                    //timeout: 3000, //server side should handle this (with good explanation)
                    params: { path: $ctrl.taskdir+"/"+$ctrl.path }
                })
                .then(function(res) {
                    $ctrl.loading = false;
                    $ctrl.files = res.data.files;
                    $ctrl.files.forEach(function(file) {
                        file.path = $ctrl.path+"/"+file.filename;
                        file.url = appconf.sca_api+"/resource/download?r="+t.resource_id+"&p="+encodeURIComponent($ctrl.taskdir+"/"+file.path)+"&at="+jwt;
                    });
                    console.dir($ctrl.files);
                }, function(res) {
                    $ctrl.loading = false;
                    if(res.data && res.data.message) toaster.error(res.data.message);
                    else toaster.error(res.statusText);
                });
            });

            /*
            //TODO - it this called for component?
            $scope.$on("$destroy", function(event) {
                if(file_timeout) $timeout.cancel(file_timeout);
            });
            */
        }
    });

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


