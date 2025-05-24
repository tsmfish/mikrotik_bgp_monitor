START
  |
  v
[Setup Logging]
  - Call setup_logging()
  |
  v
[Load Configuration]
  - Load config from 'config/config.yaml' using load_config()
  - Extract router, storage, running configs
  |
  v
[Config Loaded Successfully?]
  - Yes: Proceed
  - No: Log error -> [EXIT]
  |
  v
[Initialize Mikrotik API]
  - Create MikrotikAPI with host, username, password, port
  |
  v
[Initialize BGP Parser]
  - Create BGPParser with MikrotikAPI instance
  |
  v
[Initialize Data Structures]
  - Create empty routes_diff_history list
  - Create stop_event for threading
  |
  v
[Start Plotting Thread]
  - Launch daemon thread with update_plot(routes_diff_history, stop_event)
  |
  v
[Main Loop]
  |
  v
[Fetch BGP Data]
  - Call parser.get_bgp_data()
  |
  v
[Initialize Storage]
  - Create DataStorage with storage_config['output_path']
  - Create ChartStorage for routes and gateways
  |
  v
[Save BGP Data]
  - Call storage.save_data(bgp_data)
  - Log "Data successfully saved"
  |
  v
[Is etalon_data Empty?]
  /       \
 Yes       No
  |         |
  v         v
[Set etalon_data = bgp_data]  [Compare with Etalon Data]
  |                           - Compare sessions
  |                           - If different: Log critical
  |                           - Calculate routes_diff using levenshtein_distance(clear_routes(etalon_data["routes"]), clear_routes(bgp_data["routes"]))
  |                           - Save routes_diff to routes_chart
  |                           - If routes differ: Log critical with routes_diff
  |                           - Calculate gateway_diff using levenshtein_distance(etalon_data["gateways"], bgp_data["gateways"])
  |                           - Save gateway_diff to gateway_chart
  |                           - If gateways differ: Log critical with gateway_diff
  |                           |
  |                           v
  |                        [Set etalon_diff = routes_diff]
  |
  v
[Is previous_data Empty?]
  /       \
 Yes       No
  |         |
  v         v
[Skip Comparison]  [Compare with Previous Data]
  |                - Compare sessions
  |                - If unchanged: Log info
  |                - If different: Log critical
  |                - Calculate routes_diff using levenshtein_distance(clear_routes(previous_data["routes"]), clear_routes(bgp_data["routes"]))
  |                - Save routes_diff to routes_chart
  |                - If routes unchanged: Log info
  |                - If routes differ: Log critical with routes_diff
  |                - Calculate gateway_diff using levenshtein_distance(previous_data["gateways"], bgp_data["gateways"])
  |                - Save gateway_diff to gateway_chart
  |                - If gateways unchanged: Log info
  |                - If gateways differ: Log critical with gateway_diff
  |                |
  |                v
  |             [Set previous_diff = routes_diff]
  |
  v
[Update previous_data]
  - Set previous_data = bgp_data
  |
  v
[Append to routes_diff_history]
  - Append (etalon_diff, previous_diff) to routes_diff_history
  |
  v
[Sleep]
  - Await asyncio.sleep(running_config['interval'])
  |
  v
[KeyboardInterrupt?]
  /       \
 Yes       No
  |         |
  v         |
[Log "Monitoring stopped"]  |
  |                        |
  v                        |
[Set stop_event]           |
  |                        |
  v                        |
[Close Mikrotik API]       |
  |                        |
  v                        |
[EXIT] <------------------ [Other Exception?]
                             /       \
                           Yes       No
                            |         |
                            v         |
                         [Log Error]  |
                            |         |
                            v         |
                         [Set stop_event]
                            |
                            v
                         [Close Mikrotik API]
                            |
                            v
                          [EXIT]