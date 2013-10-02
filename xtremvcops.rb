#!/usr/bin/ruby

require 'rest-core'
require 'pp'

baseURL =  'http://10.241.105.151:42503/types/'


YourClient = RC::Builder.client do
  use RC::DefaultSite , baseURL
  use RC::JsonResponse, true
  use RC::CommonLogger, method(:puts)
  use RC::Cache       , nil, 3600
  use RC::AuthBasic     , 'mcowger', 'P@ssword1!'
end


systemsclient = YourClient.new()
allsystems = systemsclient.get("systems")

allsystems["systems"].each {
  |system|
  systemclient = YourClient.new()
  systemclient.site = baseURL + "systems/"
  systemname = system['name']
  systemid = system['href'].rpartition('/')[-1]
  mysystem = systemclient.get(systemid)
  iops = mysystem['content']['iops'].to_i()
  readiops = mysystem['content']['wr-iops'].to_i()
  writeiops = mysystem['content']['rd-riops'].to_i()
  pp systemname,systemid,iops,readiops,writeiops
}


