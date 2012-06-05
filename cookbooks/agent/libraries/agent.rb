require 'json'

module NodeAgent
  def self.update(node)
    mac = node['macaddress'].gsub(':', '')
    url = "#{node['admin']['URL']}/api/nodes/#{mac}"
    Chef::Log.debug("Sending node info to REST service at #{url}...")

    interfaces = node["network"]["interfaces"].inject([]) do |result, elm|
      result << { :name => elm[0], :addresses => elm[1]["addresses"] }
    end
    metadata = {
             :block_device => node["block_device"].to_hash,
             :interfaces => interfaces,
             :cpu => node["cpu"].to_hash,
             :memory => node["memory"].to_hash
    }

    data = { :fqdn => node["fqdn"],
             :mac => node["macaddress"],
             :ip  => node["ipaddress"],
             :metadata => metadata
    }

    headers = {"Content-Type" => "application/json"}

    cli = HTTPClient.new
    begin
      res = cli.put(url, data.to_json, headers)
      if res.status < 200 or res.status >= 300
        Chef::Log.error("HTTP PUT failed: #{res.inspect}")
      end
    rescue Exception => e
      Chef::Log.error("Error in sending node info: #{e.message}")
    end
  end
end
