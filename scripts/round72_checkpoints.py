"""Conservative same-run D7 checkpoints after the complete long queue stops."""
import round72_campaign as campaign
import round71_checkpoints as inherited

def main():
    campaign.assert_frozen();run=campaign.run
    assert not (run.OUT/'active_run.lock').exists(),'Wait until the optimizer queue stops'
    inherited.main()
    scope=run.read(run.OUT/'checkpoint_scope.json')
    scope.update(round72_wrapper_sha256=run.sha(__file__),
        horizons='300/600/1200/1800/2400/3600 for each completed D7 long run; no new solver call',
        run_identity='Round72 same-byte fresh3600s campaign',
        comparison_scope='Only these fresh same-cap runs are paired; earlier Round71 endpoints are not spliced in')
    run.write(run.OUT/'checkpoint_scope.json',scope)

if __name__=='__main__':main()
