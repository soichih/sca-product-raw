(function() {
    'use strict';

    //https://github.com/danialfarid/ng-file-upload
    var service = angular.module('sca-product-raw', [ ]);
    service.directive('scaProductRaw', function(toaster, $http, $timeout, appconf) {
        return {
            restrict: 'E',
            scope: {
                //taskid: '=',
                task: '=',
                path: '=?', //if empty, it will be set to instantce_id / task_id (relative to task dir)
            }, 
            templateUrl: 'node_modules/sca-product-raw/ui/raw.html',
            controller: function($scope) {
                function load_resource() {
                    if(!$scope.task.resource_id) return;
                    //load resource detail
                    $http.get(appconf.wf_api+"/resource/", {
                        params: {
                            find: JSON.stringify({ _id: $scope.task.resource_id })
                        }
                    }).then(function(res) {
                        if(res.data.resources && res.data.resources.length == 1) {
                            $scope.resource_detail = res.data.resources[0];
                        } else {
                            console.error("couldn't load resource detail: ");
                        }
                    }, function(res) {
                        if(res.data && res.data.message) toaster.error(res.data.message);
                        else toaster.error(res.statusText);
                    });
                }
                
                //need to load task so that I can load resource
                /*
                var t = scaTask.get($scope.taskid);
                t._promise.then(function() {
                    $scope.task = t;
                    $scope.$watch('task.resource_id', function() {          
                        //console.log("task.resource_id updated:"+t.resource_id);
                        load_resource(t.resource_id);
                    });
                });
                */
                if($scope.task.resource_id) load_resource();
                else {
                    //if resource_id is not set yet, wait for it to be set
                    $scope.$watch('task.resource_id', function() {          
                        load_resource();
                    });
                }
            }
        };
    });

    service.directive('scaProductRawDir', function(appconf, $http, toaster) {
        return {
            restrict: 'E',
            scope: {
                task: '=',
                indent: '=',
                path: '=?', //if empty, it will be set to instantce_id / task_id (relative to task dir)
            },
            templateUrl: 'node_modules/sca-product-raw/ui/dir.html',
            controller: function($scope) {
                //console.log("loading directory taskid:"+$scope.task._id);
                $scope.indent_child = $scope.indent+1;
                if(!$scope.path) $scope.path = "";

                this.getNumber = function(num) { return new Array(num); };

                $scope.taskdir = $scope.task.instance_id+"/"+$scope.task._id;
                if(!$scope.task.resource_id) {
                    console.error("sca-product-raw initialized on task with no resource_id");
                    return;
                }

                function loaddir() {
                    $scope.loading = true;
                    $http.get(appconf.wf_api+"/task/ls/"+$scope.task._id, {
                        params: { p: $scope.path }
                    })
                    .then(function(res) {
                        $scope.loading = false;
                        $scope.files = res.data.files;
                        var jwt = localStorage.getItem(appconf.jwt_id);
                        //TODO - remember file.open
                        $scope.files.forEach(function(file) {
                            file.path = "";
                            if($scope.path) file.path += $scope.path+"/";
                            file.path += file.filename;
                            file.url = appconf.wf_api+"/task/download/"+$scope.task._id+
                                "?p="+encodeURIComponent(file.path)+
                                "&at="+jwt;
                        });
                        $scope.error = null;
                    }, function(res) {
                        $scope.loading = false;
                        //ls could fail if taskdir isn't setup yet (or task starup fails).. so let's not display this to the UI
                        if(res.data && res.data.message) $scope.error = res.data.message;
                    });
                }

                loaddir();
                /*
                $scope.$watch('task.next_date', function() {          
                    //task updated.. check directory list
                    loaddir();
                });
                */ 

                $scope.download = function($event, file) {
                    $event.preventDefault();
                    window.location = file.url;
                }

                $scope.click = function(file) {
                    switch(file.attrs.mode_string[0]) {
                    case "d":
                        file.open = !file.open; break;
                    case "l":
                        alert("Traversing symbolic link is currently disabled");
                        break;
                    case "-":
                        window.location = file.url;
                    }
                }
            }
        };
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

    /* should come from sca-ng-wf
    service.filter('bytes', function() {
        return function(bytes, precision) {
            if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
            if (typeof precision === 'undefined') precision = 1;
            var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'],
                number = Math.floor(Math.log(bytes) / Math.log(1024));
            return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +  ' ' + units[number];
        }
    });
    */

    service.filter('encodeURI', function() {
      return window.encodeURIComponent;
    });
        
    //end of IIFE (immediately-invoked function expression)
})();


