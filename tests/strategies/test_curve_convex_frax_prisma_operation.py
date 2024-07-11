from ape import Contract, chain
from utils import harvest_strategy, increase_time, check_status, ZERO_ADDRESS
import pytest
import ape

# this test makes sure we can use keepCVX and keepCRV
def test_keep(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    voter,
    crv,
    fxs,
    amount,
    sleep_time,
    convex_token,
    no_profit,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    which_strategy,
    new_proxy,
    yprisma,
):
    # don't do for FXN, no keep
    if which_strategy == 3:
        print("\n🚫 FXN strategy has no keep, skipping...\n")
        return

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount, sender=whale)

    # harvest as-is before we have yield to hit all parts of our if statement
    if which_strategy == 0:
        # need to set voters first if we're trying to set keep
        with ape.reverts():
            strategy.setLocalKeepCrvs(1000, 1000, sender=gov)
        strategy.setVoters(gov, gov, sender=gov)
        strategy.setLocalKeepCrvs(1000, 1000, sender=gov)
    elif which_strategy == 1:
        strategy.setVoter(ZERO_ADDRESS, sender=gov)
        # need to set voters first if we're trying to set keep
        with ape.reverts():
            strategy.setLocalKeepCrv(1000, sender=gov)
        strategy.setVoter(voter, sender=gov)
        strategy.setLocalKeepCrv(1000, sender=gov)
    elif which_strategy == 2:
        # need to set voters first if we're trying to set keep
        with ape.reverts():
            strategy.setLocalKeepCrvs(1000, 1000, 1000, sender=gov)
        strategy.setVoters(gov, gov, gov, sender=gov)
        strategy.setLocalKeepCrvs(1000, 1000, 1000, sender=gov)
    else:
        with ape.reverts():
            strategy.setLocalKeepCrvs(1000, 1000, 1000, sender=gov)
        with ape.reverts():
            strategy.setLocalKeepCrvs(0, 1000, 1000, sender=gov)
        with ape.reverts():
            strategy.setLocalKeepCrvs(0, 0, 1000, sender=gov)
        strategy.setVoters(gov, gov, gov, sender=gov)
        strategy.setLocalKeepCrvs(1000, 1000, 1000, sender=gov)

    # harvest our funds in
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep to get some profit
    increase_time(chain, sleep_time)

    # normal operation
    if which_strategy == 0:
        treasury_before = convex_token.balanceOf(strategy.convexVoter())

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = convex_token.balanceOf(strategy.convexVoter())
        if not no_profit:
            assert treasury_after > treasury_before
    elif which_strategy == 1:
        treasury_before = crv.balanceOf(strategy.curveVoter())

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = crv.balanceOf(strategy.curveVoter())
        if not no_profit:
            assert treasury_after > treasury_before
    elif which_strategy == 2:
        treasury_before = yprisma.balanceOf(strategy.yprismaVoter())

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = yprisma.balanceOf(strategy.yprismaVoter())
        if not no_profit:
            assert treasury_after > treasury_before
    else:
        treasury_before = fxs.balanceOf(strategy.fraxVoter())

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = fxs.balanceOf(strategy.fraxVoter())
        if not no_profit:
            assert treasury_after > treasury_before

    # keepCRV off only
    if which_strategy == 0:
        strategy.setLocalKeepCrvs(0, 0, sender=gov)
        treasury_before = convex_token.balanceOf(strategy.convexVoter())

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = convex_token.balanceOf(strategy.convexVoter())
        assert treasury_after == treasury_before
    elif which_strategy == 1:
        strategy.setLocalKeepCrv(0, sender=gov)
        treasury_before = crv.balanceOf(strategy.curveVoter())

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = crv.balanceOf(strategy.curveVoter())
        assert treasury_after == treasury_before
    elif which_strategy == 2:
        strategy.setLocalKeepCrvs(0, 0, 0, sender=gov)
        treasury_before = crv.balanceOf(strategy.curveVoter())

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = crv.balanceOf(strategy.curveVoter())
        assert treasury_after == treasury_before
    else:
        strategy.setLocalKeepCrvs(0, 0, 0, sender=gov)
        strategy.setVoters(gov, gov, gov, sender=gov)
        treasury_before = fxs.balanceOf(strategy.fraxVoter())

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = fxs.balanceOf(strategy.fraxVoter())
        assert treasury_after == treasury_before

    # voter off only
    if which_strategy == 0:
        strategy.setLocalKeepCrvs(1000, 1000, sender=gov)
        strategy.setVoters(ZERO_ADDRESS, ZERO_ADDRESS, sender=gov)

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    elif which_strategy == 1:
        strategy.setLocalKeepCrv(1000, sender=gov)
        strategy.setVoter(ZERO_ADDRESS, sender=gov)

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    else:
        strategy.setLocalKeepCrvs(1000, 1000, 1000, sender=gov)
        strategy.setVoters(ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, sender=gov)

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    # both off
    if which_strategy == 0:
        strategy.setLocalKeepCrvs(0, 0, sender=gov)

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    elif which_strategy == 1:
        strategy.setLocalKeepCrv(0, sender=gov)

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    else:
        strategy.setLocalKeepCrvs(0, 0, 0, sender=gov)

        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )


# this tests having multiple rewards tokens on our strategy proxy
def test_proxy_rewards(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    voter,
    crv,
    fxs,
    amount,
    sleep_time,
    convex_token,
    no_profit,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    which_strategy,
    new_proxy,
    has_rewards,
):
    # only do for curve strat
    if which_strategy != 1 or not has_rewards:
        print("\nNot Curve strategy and/or no extra rewards token\n")
        return

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount, sender=whale)
    newWhale = token.balanceOf(whale)

    # harvest funds in
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # simulate profits
    increase_time(chain, sleep_time)

    # add a second rewards token to our array, doesn't matter what
    second_reward_token = fxs
    fxs_whale = accounts.at("0xc8418aF6358FFddA74e09Ca9CC3Fe03Ca6aDC5b0", force=True)
    fxs.transfer(voter, 100e18, sender=fxs_whale)
    new_proxy.approveRewardToken(second_reward_token, sender=gov)
    strategy.updateRewards([rewards_token, second_reward_token], sender=gov)
    assert fxs.balanceOf(voter) > 0

    # harvest
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert fxs.balanceOf(voter) == 0

    crv_balance = crv.balanceOf(strategy)
    assert crv_balance > 0
    print("CRV Balance:", crv_balance / 1e18)

    rewards_balance = rewards_token.balanceOf(strategy)
    assert rewards_balance > 0
    print("Rewards Balance:", rewards_balance / 1e18)

    rewards_balance_too = second_reward_token.balanceOf(strategy)
    assert rewards_balance_too > 0
    print("Second Rewards Token Balance:", rewards_balance_too / 1e18)


# lower our number of keks
def test_lower_keks(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount / 20, sender=whale)
    newWhale = token.balanceOf(whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # can't do this yet since we're still locked
    with ape.reverts():
        strategy.setMaxKeks(3, sender=gov)

    # can't withdraw everything right now
    with ape.reverts():
        vault.withdraw(sender=whale)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)

    tx = strategy.harvest(sender=gov)
    increase_time(chain, 1)

    # can't set to zero
    with ape.reverts():
        strategy.setMaxKeks(0, sender=gov)

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # can't harvest again as funds are locked, but only if we have something to harvest in
    with ape.reverts():
        vault.deposit(amount / 20, sender=whale)
        (profit, loss, extra) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    # sleep for 4 more days to fully unlock our first two keks
    increase_time(chain, 86400)
    with ape.reverts():
        strategy.setMaxKeks(4, sender=gov)
        print("Wait for more unlock to lower the number of keks we have")
    increase_time(chain, 86400 * 3)
    strategy.setMaxKeks(4, sender=gov)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])

    # try to decrease our max keks again
    with ape.reverts():
        strategy.setMaxKeks(2, sender=gov)
        print("Wait for unlock to lower the number of keks we have")

    # wait another week so our frax LPs are unlocked
    increase_time(chain, 86400 * 7)

    # check how much locked stake we have (should be zero)
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])

    # lower now
    strategy.setMaxKeks(3, sender=gov)
    print("Keks successfullly lowered to 3")

    # withdraw everything
    vault.withdraw(sender=whale)

    # should still be able to lower keks when strategy is empty
    strategy.setMaxKeks(1, sender=gov)


# lower our number of keks after we get well above our maxKeks
def test_lower_keks_part_two(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    # lower it immediately
    strategy.setMaxKeks(3, sender=gov)

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount / 20, sender=whale)
    newWhale = token.balanceOf(whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep since our 3 keks are full
    increase_time(chain, 86400 * 7)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep to free them all up
    increase_time(chain, 86400 * 7)

    # lower down to 2, this should hit the other branch in our setMaxKeks
    strategy.setMaxKeks(2, sender=gov)


# increase our number of keks
def test_increase_keks(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount / 20, sender=whale)
    newWhale = token.balanceOf(whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # increase our max keks to 7
    strategy.setMaxKeks(7, sender=gov)
    print("successfully increased our keks")


# withdraw from the only unlocked kek
def test_withdraw_with_some_locked(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount / 20, sender=whale)
    newWhale = token.balanceOf(whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # sleep for 3 more days to fully unlock our first kek
    increase_time(chain, 86400 * 3)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # withdraw from our first kek
    vault.withdraw(1e18, sender=whale)


# test manual withdrawals
def test_manual_withdrawal(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount / 20, sender=whale)
    newWhale = token.balanceOf(whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # test withdrawing 1 kek manually at a time
    assert strategy.balanceOfWant() == profit_amount
    index_to_withdraw = strategy.kekInfo()["nextKek"] - 1

    # can't withdraw yet, need to wait
    with ape.reverts():
        strategy.manualWithdraw(index_to_withdraw, sender=gov)

    increase_time(chain, 86400 * 7)

    strategy.manualWithdraw(index_to_withdraw, sender=gov)
    assert strategy.balanceOfWant() > 0


# lower our number of keks
def test_lower_keks_add_to_existing(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    # set it so we don't add new keks and only deposit to existing ones, once we reach our max
    strategy.setDepositParams(1e18, 5_000_000e18, True, sender=gov)

    # since we do so many harvests here, reduce our profit_amount
    profit_amount = profit_amount / 2.5

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount / 20, sender=whale)
    newWhale = token.balanceOf(whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # can't do this yet since we're still locked
    with ape.reverts():
        strategy.setMaxKeks(3, sender=gov)

    # can't withdraw everything right now
    with ape.reverts():
        vault.withdraw(sender=whale)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)

    tx = strategy.harvest(sender=gov)
    increase_time(chain, 1)

    # can't set to zero
    with ape.reverts():
        strategy.setMaxKeks(0, sender=gov)

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # can't harvest again as funds are locked, but only if we have something to harvest in
    # ^^ this is from the normal test, obvs not true here
    vault.deposit(amount / 20, sender=whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep for 4 more days to fully unlock our first two keks
    increase_time(chain, 86400)
    with ape.reverts():
        strategy.setMaxKeks(4, sender=gov)
        print("Wait for more unlock to lower the number of keks we have")
    increase_time(chain, 86400 * 3)
    strategy.setMaxKeks(4, sender=gov)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])

    # try to decrease our max keks again
    # ^^ again, doesn't revert like we expect since it's no longer new locking
    strategy.setMaxKeks(2, sender=gov)
    print("Wait for unlock to lower the number of keks we have")

    # wait another week so our frax LPs are unlocked
    increase_time(chain, 86400 * 7)

    # check how much locked stake we have (should be zero)
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])

    # lower now
    strategy.setMaxKeks(3, sender=gov)
    print("Keks successfullly lowered to 3")

    # withdraw everything
    vault.withdraw(sender=whale)

    # should still be able to lower keks when strategy is empty
    strategy.setMaxKeks(1, sender=gov)


# lower our number of keks after we get well above our maxKeks
def test_lower_keks_part_two_add_to_existing(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    # set it so we don't add new keks and only deposit to existing ones, once we reach our max
    strategy.setDepositParams(1e18, 5_000_000e18, True, sender=gov)

    # lower it immediately
    strategy.setMaxKeks(3, sender=gov)

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount / 20, sender=whale)
    newWhale = token.balanceOf(whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep since our 3 keks are full
    increase_time(chain, 86400 * 7)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep to free them all up
    increase_time(chain, 86400 * 7)

    # lower down to 2, this should hit the other branch in our setMaxKeks
    strategy.setMaxKeks(2, sender=gov)


# increase our number of keks
def test_increase_keks_add_to_existing(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    # set it so we don't add new keks and only deposit to existing ones, once we reach our max
    strategy.setDepositParams(1e18, 5_000_000e18, True, sender=gov)

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount / 20, sender=whale)
    newWhale = token.balanceOf(whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # increase our max keks to 7
    strategy.setMaxKeks(7, sender=gov)
    print("successfully increased our keks")


# increase our number of keks
def test_keks_add_to_existing(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    # set it so we don't add new keks and only deposit to existing ones, once we reach our max
    strategy.setDepositParams(1e18, 5_000_000e18, True, sender=gov)

    # since we do so many harvests here, reduce our profit_amount
    profit_amount = profit_amount / 2.5

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount / 20, sender=whale)
    newWhale = token.balanceOf(whale)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    next_kek = strategy.kekInfo()["nextKek"]
    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    staking = Contract(strategy.stakingAddress())

    # make sure that a different kek is increasing in size each time
    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())

    # check visually that we are adding to a different kek each time using the output printout
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, sender=whale)
    increase_time(chain, 86400)
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5
    increase_time(chain, 86400 * 5)

    # whale should be able to withdraw all of his funds now
    vault.withdraw(sender=whale)
    assert vault.totalAssets() == 0


def test_yprisma_claim(
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
    yprisma,
    which_strategy,
):
    # only for prisma
    if which_strategy != 2:
        print("\n🚫🌈 Not a PRISMA strategy, skipping...\n")
        return

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount, sender=whale)

    # set this to false so we allow yPRISMA to accumulate in the strategy
    use_yswaps = False

    receiver = Contract(strategy.prismaReceiver())
    eid = receiver.emissionId()
    prisma_vault = Contract(strategy.prismaVault())
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    claimable = receiver.claimableReward(strategy).items()
    # Check if any non-zero values (shouldn't have any, should have small amounts for all assets)
    assert any(x for x in (claimable if isinstance(claimable, tuple) else (claimable,)))

    increase_time(chain, sleep_time)

    # check that we have claimable profit, need this for min and max profit checks below
    claimable_profit = strategy.claimableProfitInUsdc()
    assert claimable_profit > 0
    print("🤑 Claimable profit >0:", claimable_profit / 1 * 10**6)

    # set our max delay to 1 seconds less than sleep time so we trigger true, then set it back to 21 days
    strategy.setMaxReportDelay(sleep_time - 1, sender=gov)
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True
    strategy.setMaxReportDelay(86400 * 21, sender=gov)

    # we have tiny profit but that's okay; our triggers should be false because we don't have max boost
    # update our minProfit so our harvest should trigger true
    # will be true/false same as above based on max boost
    strategy.setHarvestTriggerParams(1, 1000000 * 10**6, sender=gov)
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be false.", tx)
    assert tx == strategy.claimsAreMaxBoosted()

    # update our maxProfit, should again follow our max boost check
    strategy.setHarvestTriggerParams(1000000 * 10**6, 1, sender=gov)
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be false.", tx)
    assert tx == strategy.claimsAreMaxBoosted()

    # force claim so we should be true
    strategy.setClaimParams(True, True, sender=vault.governance())
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    # turn off claiming entirely
    strategy.setClaimParams(False, False, sender=vault.governance())
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be false.", tx)
    assert tx == False
    strategy.setClaimParams(False, True, sender=vault.governance())

    strategy.setHarvestTriggerParams(2000 * 10**6, 25000 * 10**6, sender=gov)

    # turn on the force claim
    strategy.setClaimParams(True, True, sender=vault.governance())

    # update our minProfit so our harvest triggers true
    strategy.setHarvestTriggerParams(1, 1000000 * 10**6, sender=gov)
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    # turn off claiming entirely
    strategy.setClaimParams(True, False, sender=vault.governance())
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be false.", tx)
    assert tx == False
    strategy.setClaimParams(True, True, sender=vault.governance())

    # update our maxProfit so harvest triggers true
    strategy.setHarvestTriggerParams(1000000 * 10**6, 1, sender=gov)
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    strategy.setHarvestTriggerParams(2000 * 10**6, 25000 * 10**6, sender=gov)

    # set our max delay to 1 day so we trigger true, then set it back to 21 days
    strategy.setMaxReportDelay(sleep_time - 1, sender=gov)
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be True.", tx)
    assert tx == True
    strategy.setMaxReportDelay(86400 * 21, sender=gov)

    strategy.setClaimParams(False, True, sender=vault.governance())

    # Now harvest again
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    # This only works if we have exhausted our boost for current week (we won't have claimed any yPRISMA)
    if not strategy.claimsAreMaxBoosted():
        assert yprisma.balanceOf(strategy) == 0
    else:
        assert yprisma.balanceOf(strategy) > 0

    # sleep to get to the new epoch
    increase_time(chain, 60 * 60 * 24 * 7)

    claimable_profit = strategy.claimableProfitInUsdc()
    assert claimable_profit > 0
    print("🤑 Claimable profit next epoch:", claimable_profit / 1 * 10**6)

    # give accounts some ETH
    receiver.balance += 10 * 10**18

    prisma_vault.allocateNewEmissions(eid, sender=receiver)
    receiver.claimableReward(strategy)
    y = "0x90be6DFEa8C80c184C442a36e17cB2439AAE25a7"
    boosted = prisma_vault.getClaimableWithBoost(y)
    assert boosted[0] > 0
    assert strategy.claimsAreMaxBoosted()

    # now we should be able to claim without forcing
    # update our minProfit so our harvest triggers true
    strategy.setHarvestTriggerParams(1, 1000000 * 10**6, sender=gov)
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    # update our maxProfit so harvest triggers true
    strategy.setHarvestTriggerParams(1000000 * 10**6, 1, sender=gov)
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    # we shouldn't get any more yPRISMA if we turn off claims, but we may have received some above if we were max boosted
    before = yprisma.balanceOf(strategy)
    strategy.setClaimParams(False, False, sender=vault.governance())

    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    # extra should still be zero since we don't enter yswaps
    assert yprisma.balanceOf(strategy) == before
    assert extra == 0

    # turn claiming back on
    strategy.setClaimParams(False, True, sender=vault.governance())

    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    assert yprisma.balanceOf(strategy) > before


def test_yprisma_force_claim(
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
    yprisma,
    which_strategy,
):
    # only for prisma
    if which_strategy != 2:
        print("\n🚫🌈 Not a PRISMA strategy, skipping...\n")
        return

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount, sender=whale)

    # set this to false so we allow yPRISMA to accumulate in the strategy
    use_yswaps = False

    receiver = Contract(strategy.prismaReceiver())
    eid = receiver.emissionId()
    prisma_vault = Contract(strategy.prismaVault())
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    claimable = receiver.claimableReward(strategy).items()
    # Check if any non-zero values (shouldn't have any, should have small amounts for all assets)
    assert any(x for x in (claimable if isinstance(claimable, tuple) else (claimable,)))

    increase_time(chain, sleep_time)

    # force claim from convex's receiver
    assert yprisma.balanceOf(strategy) == 0
    convex_delegate = "0x8ad7a9e2B3Cd9214f36Cb871336d8ab34DdFdD5b"
    strategy.claimRewards(convex_delegate, 5000, sender=vault.governance())
    assert yprisma.balanceOf(strategy) > 0
    balance_1 = yprisma.balanceOf(strategy)

    # sleep to get to the new epoch
    increase_time(chain, 60 * 60 * 24 * 7)

    # turn off claims to not add any more yprisma with the next harvest
    strategy.setClaimParams(False, False, sender=vault.governance())

    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )

    # extra will be zero here since we're not using yswaps
    assert extra == 0
    assert yprisma.balanceOf(strategy) == balance_1

    # turn claiming back on
    strategy.setClaimParams(False, True, sender=vault.governance())

    claimable_profit = strategy.claimableProfitInUsdc()
    assert claimable_profit > 0
    print("🤑 Claimable profit next epoch:", claimable_profit / 1 * 10**6)

    # give accounts some ETH
    receiver.balance += 10 * 10**18

    prisma_vault.allocateNewEmissions(eid, sender=receiver)
    receiver.claimableReward(strategy)
    y = "0x90be6DFEa8C80c184C442a36e17cB2439AAE25a7"
    boosted = prisma_vault.getClaimableWithBoost(y)
    assert boosted[0] > 0
    assert strategy.claimsAreMaxBoosted()
    assert yprisma.balanceOf(strategy) > 0
    use_yswaps = True

    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )

    # we should have earned more than we had before
    assert extra > balance_1

    # and we should have cleared out our yprisma sitting in the strategy (sold it all)
    assert yprisma.balanceOf(strategy) == 0


def test_yprisma_trigger_claim(
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
    yprisma,
    which_strategy,
):
    # only for prisma
    if which_strategy != 2:
        print("\n🚫🌈 Not a PRISMA strategy, skipping...\n")
        return

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount, sender=whale)

    # turn off default claiming, this is how we will function realistically most of the time
    strategy.setClaimParams(False, False, sender=gov)

    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )

    # sleep to get some profit
    increase_time(chain, sleep_time)

    assert strategy.claimableProfitInUsdc() > 0

    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )

    # make sure we didn't claim yprisma
    assert extra == 0

    # make sure our harvest trigger is false
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be false.", tx)
    assert tx == False

    # trigger claim from convex's receiver
    assert yprisma.balanceOf(strategy) == 0
    assert strategy.claimParams()["forceClaimOnce"] == False
    assert strategy.claimParams()["shouldClaimRewards"] == False
    assert strategy.claimParams()["boostDelegate"] == ZERO_ADDRESS
    assert strategy.claimParams()["maxFee"] == 0

    convex_delegate = "0x8ad7a9e2B3Cd9214f36Cb871336d8ab34DdFdD5b"
    max_fee = 5000
    strategy.triggerClaimRewards(convex_delegate, max_fee, sender=gov)

    # trigger should be true
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    assert strategy.claimParams()["forceClaimOnce"] == False
    assert strategy.claimParams()["shouldClaimRewards"] == False
    assert strategy.claimParams()["boostDelegate"] == convex_delegate
    assert strategy.claimParams()["maxFee"] == max_fee

    # shouldn't have affected balance
    assert yprisma.balanceOf(strategy) == 0

    # harvesting should claim yprisma
    (profit, loss, extra) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    assert extra > 0

    # and values should be reset
    assert strategy.claimParams()["forceClaimOnce"] == False
    assert strategy.claimParams()["shouldClaimRewards"] == False
    assert strategy.claimParams()["boostDelegate"] == ZERO_ADDRESS
    assert strategy.claimParams()["maxFee"] == 0

    # make sure our harvest trigger is false
    tx = strategy.harvestTrigger(0)
    print("\nShould we harvest? Should be false.", tx)
    assert tx == False
