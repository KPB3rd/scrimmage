How to use parameter analysis tool:

- Templatize the targeted mission file.

    After choosing the scrimmage mission file, you need to decide the parameters of the mission that you want optimized.
    In your mission file, insert environment variable notation, e.g. ${example}, for the chosen parameters. For example:
        <autonomy order="2" 
              weight_priority="${w_pr}" weight_pk="${w_pk}"
              weight_dist="${w_dist}"    dist_decay="${w_dist_decay}"> AuctionPlugin
        </autonomy>

    In the above example, parameters w_pr, w_pk, w_dist, and w_dist_decay will be optimized by this tool. 
    Keep in mind the more parameters you choose, the more difficult the analysis.

- Configure settings.json.

    Define the mission file and log path.

    The StateSpaceSampler is used to create an initial exploratory sampling of the parameter space. 
    Currently only Latin Hypercube Sampling is supported. LHS will choose N orthogonal parameter samples, providing a good initial exploration.





