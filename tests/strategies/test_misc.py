from ape import Contract, chain
from utils import harvest_strategy, increase_time, check_status
import pytest
import ape


# test removing a strategy from the withdrawal queue
def test_remove_from_withdrawal_queue(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    sleep_time,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
):
    ## deposit to the vault after approving
    starting_whale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount, sender=whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # simulate earnings, harvest
    increase_time(chain, sleep_time)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # removing a strategy from the queue shouldn't change its assets
    before = strategy.estimatedTotalAssets()
    vault.removeStrategyFromQueue(strategy, sender=gov)
    after = strategy.estimatedTotalAssets()
    assert before == after

    # check that our strategy is no longer in the withdrawal queue's 20 addresses
    addresses = []
    for x in range(19):
        address = vault.withdrawalQueue(x)
        addresses.append(address)
    print(
        "Strategy Address: ",
        strategy.address,
        "\nWithdrawal Queue Addresses: ",
        addresses,
    )
    assert not strategy.address in addresses


# test revoking a strategy from the vault
def test_revoke_strategy_from_vault(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    is_slippery,
    no_profit,
    sleep_time,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    RELATIVE_APPROX,
    which_strategy,
):

    ## deposit to the vault after approving
    starting_whale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount, sender=whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep to earn some yield
    increase_time(chain, sleep_time)

    # record our assets everywhere
    vault_assets_starting = vault.totalAssets()
    vault_holdings_starting = token.balanceOf(vault)
    strategy_starting = strategy.estimatedTotalAssets()

    # revoke and harvest
    vault.revokeStrategy(strategy.address, sender=gov)

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        increase_time(chain, 86400 * 7)

    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # harvest again to get the last of our profit with ySwaps
    if use_yswaps:
        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        # check our current status
        print("\nAfter yswaps extra harvest")
        strategy_params = check_status(strategy, vault)

        # make sure we recorded our gain properly
        if not no_profit:
            assert profit > 0

    # confirm we made money, or at least that we have about the same
    vault_assets_after_revoke = vault.totalAssets()
    strategy_assets_after_revoke = strategy.estimatedTotalAssets()

    if no_profit:
        assert (
            pytest.approx(vault_assets_after_revoke, rel=RELATIVE_APPROX)
            == vault_assets_starting
        )
        assert (
            pytest.approx(token.balanceOf(vault), rel=RELATIVE_APPROX)
            == vault_holdings_starting + strategy_starting
        )
    else:
        assert vault_assets_after_revoke > vault_assets_starting
        assert token.balanceOf(vault) > vault_holdings_starting + strategy_starting

    # should be zero in our strategy
    assert pytest.approx(strategy_assets_after_revoke, rel=RELATIVE_APPROX) == 0

    # simulate five days of waiting for share price to bump back up
    increase_time(chain, 86400 * 5)

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        increase_time(chain, 86400 * 7)

    # withdraw and confirm we made money, or at least that we have about the same (profit whale has to be different from normal whale)
    vault.withdraw(sender=whale)
    if no_profit:
        assert (
            pytest.approx(token.balanceOf(whale), rel=RELATIVE_APPROX) == starting_whale
        )
    else:
        assert token.balanceOf(whale) > starting_whale


# test the setters on our strategy
def test_setters(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    which_strategy,
    use_yswaps,
    profit_whale,
    profit_amount,
    target,
    strategist,
    tests_using_tenderly,
):
    # deposit to the vault after approving
    starting_whale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount, sender=whale)
    name = strategy.name()

    # test our setters in baseStrategy
    strategy.setMaxReportDelay(10**18, sender=gov)
    strategy.setMinReportDelay(100, sender=gov)
    strategy.setRewards(gov, sender=gov)
    strategy.setStrategist(gov, sender=gov)

    ######### BELOW WILL NEED TO BE UPDATED BASED SETTERS OUR STRATEGY HAS #########
    # special setter for frax
    if which_strategy == 4:
        strategy.setLockTime(90000 * 7, sender=gov)

        if not tests_using_tenderly:
            # whale can't call
            with ape.reverts():
                strategy.setLockTime(90000, sender=whale)
            # can't be too short
            with ape.reverts():
                strategy.setLockTime(100, sender=gov)
            # or too long
            with ape.reverts():
                strategy.setLockTime(2**256 - 1, sender=gov)

        # set our deposit params
        maxToStake = amount * 0.75
        minToStake = 100
        strategy.setDepositParams(minToStake, maxToStake, False, sender=gov)
        with ape.reverts():
            strategy.setDepositParams(maxToStake, minToStake, False, sender=gov)

    # harvest our credit
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    if which_strategy == 4:
        total_staked = strategy.stakedBalance()
        assert total_staked == maxToStake
        assert strategy.estimatedTotalAssets() > total_staked

        # get the rest of our funds staked
        increase_time(chain, 1)

        strategy.setDepositParams(10**21, 10**29, False, sender=gov)
        strategy.harvest(sender=gov)
        assert strategy.estimatedTotalAssets() >= amount

    # check that we have claimable rewards, have to call for frax tho
    if which_strategy == 4:
        increase_time(chain, 86400 * 7)

        profit = strategy.claimableProfitInUsdc.call()
        assert profit > 0
        print("Claimable Profit:", profit / 10**6)
    elif which_strategy == 0:
        increase_time(chain, 86400 * 7)

        profit = strategy.claimableProfitInUsdc()
        assert profit > 0
        print("Claimable Profit:", profit / 10**6)

    if which_strategy == 0:
        strategy.setVoters(gov, gov, sender=gov)
        strategy.setLocalKeepCrvs(10, 10, sender=gov)
        strategy.setClaimRewards(True, sender=gov)

        if not tests_using_tenderly:
            # test our reverts as well
            with ape.reverts():
                strategy.setLocalKeepCrvs(1000000, 0, sender=gov)
            with ape.reverts():
                strategy.setLocalKeepCrvs(0, 100000000, sender=gov)
    elif which_strategy == 1:
        strategy.setVoter(gov, sender=gov)
        strategy.setLocalKeepCrv(10, sender=gov)

        if not tests_using_tenderly:
            # test our reverts as well
            with ape.reverts():
                strategy.setLocalKeepCrv(1000000, sender=gov)

    if which_strategy == 2:
        strategy.setVoters(gov, gov, gov, sender=gov)
        strategy.setLocalKeepCrvs(10, 10, 10, sender=gov)
        if not tests_using_tenderly:
            # test our reverts as well
            with ape.reverts():
                strategy.setLocalKeepCrvs(1000000, 0, 0, sender=gov)
            with ape.reverts():
                strategy.setLocalKeepCrvs(0, 100000000, 0, sender=gov)

    elif which_strategy == 4:
        strategy.setVoters(gov, gov, gov, sender=gov)
        strategy.setLocalKeepCrvs(10, 10, 10, sender=gov)

        if not tests_using_tenderly:
            # test our reverts as well
            with ape.reverts():
                strategy.setLocalKeepCrvs(1000000, 0, 0, sender=gov)
            with ape.reverts():
                strategy.setLocalKeepCrvs(0, 100000000, 0, sender=gov)
            with ape.reverts():
                strategy.setLocalKeepCrvs(0, 0, 10000000, sender=gov)

    strategy.setStrategist(strategist, sender=gov)
    name = strategy.name()
    print("Strategy Name:", name)


# test sweeping out tokens
def test_sweep(
    gov,
    token,
    vault,
    whale,
    strategy,
    to_sweep,
    amount,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    tests_using_tenderly,
):
    # deposit to the vault after approving
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount, sender=whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # we can sweep out non-want tokens
    strategy.sweep(to_sweep, sender=gov)

    # Strategy want token doesn't work
    token.transfer(strategy.address, amount, sender=whale)
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0

    if not tests_using_tenderly:
        with ape.reverts("revert: !want"):
            strategy.sweep(token, sender=gov)
        with ape.reverts():
            strategy.sweep(to_sweep, sender=whale)

        # Vault share token doesn't work
        with ape.reverts("revert: !shares"):
            strategy.sweep(vault.address, sender=gov)
