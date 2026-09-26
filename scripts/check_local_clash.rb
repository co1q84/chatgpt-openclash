#!/usr/bin/env ruby
# Local, credential-safe checks for the private profiles (not published in Git).
# Usage: ruby scripts/check_local_clash.rb openclash.yaml forstash.yaml forandroid.yaml
require 'yaml'
require 'uri'

files = ARGV.empty? ? %w[openclash.yaml forstash.yaml forandroid.yaml] : ARGV
failures = []
files.each do |file|
  config = YAML.load_file(file)
  nodes = config.fetch('proxies').to_h { |p| [p.fetch('name'), p] }
  groups = config.fetch('proxy-groups').to_h { |p| [p.fetch('name'), p] }
  check = lambda do |condition, message|
    failures << "#{File.basename(file)}: #{message}" unless condition
  end

  # Follow every user-selectable route, rather than just checking group names.
  visit = lambda do |name, seen|
    return false if seen.include?(name)
    if groups.key?(name)
      group = groups[name]
      members = group.fetch('proxies', [])
      return false unless group.fetch('use', []).empty? && !members.empty?
      return members.all? { |child| visit.call(child, seen + [name]) }
    end
    %w[BOX_VISION FALL_BOX].include?(name)
  end
  check.call(visit.call('PROXY', []), 'PROXY exposes an exit that bypasses the VPS')
  check.call(groups.fetch('BOX_FIRST')['type'] == 'fallback' &&
             groups.fetch('BOX_FIRST')['proxies'] == %w[BOX_VISION FALL_BOX],
             'VPS direct path must be preferred over the relayed path')
  check.call(nodes.fetch('BOX_VISION')['dialer-proxy'].nil?, 'direct VPS path uses a relay')
  check.call(nodes.fetch('FALL_BOX')['dialer-proxy'] == 'BEST_JC', 'backup bypasses airport relay')
  check.call(nodes.fetch('FALL_BOX')['server'] == nodes.fetch('BOX_VISION')['server'],
             'primary and backup no longer use the same VPS')
  check.call(nodes.fetch('FALL_BOX')['cipher'] == '2022-blake3-aes-256-gcm',
             'backup lost the encrypted device-to-VPS transport')
  check.call(groups.fetch('BOX_FIRST').fetch('interval', 600) <= 120 &&
             groups.fetch('BOX_FIRST')['lazy'] == false, 'full-chain checks can remain stale')

  dns = config.fetch('dns')
  stash = File.basename(file).include?('stash')
  domestic = %w[https://doh.pub/dns-query https://dns.alidns.com/dns-query]
  overseas = %w[https://dns.google/dns-query https://cloudflare-dns.com/dns-query]
  policies = dns.fetch('nameserver-policy')
  if stash
    check.call(dns['follow-rule'] == true, 'Stash DNS does not follow the VPS route')
    %w[dns.google cloudflare-dns.com].each do |host|
      # DNS endpoint rules must precede general domain/IP rules.
      check.call(config.fetch('rules').index("DOMAIN,#{host},BOX_FIRST")&.<(
                   config.fetch('rules').index('RULE-SET,ai,PROXY') || 0),
                 'overseas DNS is not pinned to the VPS before broad routing')
    end
    %w[geosite:gfw geosite:geolocation-!cn].each do |key|
      check.call(policies[key] == overseas, 'Stash overseas DNS policy is missing')
    end
  else
    policies.each do |_, servers|
      Array(servers).each do |server|
        next unless overseas.any? { |url| server.start_with?(url) }
        check.call(server.end_with?('#BOX_FIRST'), 'overseas DNS is not pinned to the VPS')
      end
    end
    check.call(Array(dns['direct-nameserver']).all? { |s| s.end_with?('#DIRECT') },
               'direct destination DNS is not explicitly local')
  end
  check.call(domestic.all? { |s| Array(dns['nameserver']).include?(stash ? s : "#{s}#DIRECT") },
             'default domestic resolution was displaced')
  check.call(!Array(dns['proxy-server-nameserver']).empty?, 'proxy bootstrap DNS is missing')

  # Downloading the airport subscription must not depend on a working VPS.
  config.fetch('proxy-providers').each_value do |provider|
    host = URI.parse(provider.fetch('url')).host
    check.call(config.fetch('rules').first(15).include?("DOMAIN,#{host},DIRECT"),
               'subscription download lacks an early direct bootstrap route')
    check.call(policies.key?(host), 'subscription hostname lacks bootstrap DNS policy')
  end
end
if failures.empty?
  puts "PASS: #{files.length} profiles: VPS-only exits, relay, failover checks and DNS bootstrap"
else
  warn failures.join("\n")
  exit 1
end
