import json
from src.utils import clear_routes, net_addr_to_int, levenshtein_distance


def main(l_file_name: str, r_file_name: str):
        l_value_raw = json.load(open(l_file_name))
        r_value_raw = json.load(open(r_file_name))

        l_value, r_value = (clear_routes(l_value_raw.get("routes", [])),
                                clear_routes(r_value_raw.get("routes", [])))
        l_value.sort(key=lambda x: net_addr_to_int(x[0]))
        r_value.sort(key=lambda x: net_addr_to_int(x[0]))

        distance = levenshtein_distance(l_value, r_value)
        pass

if __name__ == "__main__":
    main(u"data/20250517_182919_bgp_data.json   ", "data/20250517_182920_bgp_data.json")
