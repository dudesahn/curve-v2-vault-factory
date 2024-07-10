from ape import Contract, chain
from utils import harvest_strategy, increase_time, check_status, ZERO_ADDRESS
import pytest
import ape


# test our permissionless swaps and our trade handler functions as intended
def test_keepers_and_trade_handler(
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
    keeper_wrapper,
    trade_factory,
    crv_whale,
    which_strategy,
    tests_using_tenderly,
    yprisma,
    fxn_whale,
):
    # no testing needed if we're not using yswaps
    if not use_yswaps:
        return

    ## deposit to the vault after approving
    starting_whale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, sender=whale)
    vault.deposit(amount, sender=whale)
    newWhale = token.balanceOf(whale)

    # harvest, store asset amount
    (profit, loss) = harvest_strategy(
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

    # harvest, store new asset amount
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # set our keeper up
    strategy.setKeeper(keeper_wrapper, sender=gov)

    # here we make sure we can harvest through our keeper wrapper
    keeper_wrapper.harvest(strategy, sender=profit_whale)
    print("Keeper wrapper harvest works")

    ####### ADD LOGIC AS NEEDED FOR SENDING REWARDS TO STRATEGY #######
    # send our strategy some CRV. normally it would be sitting waiting for trade handler but we automatically process it
    crv_whale.balance += 10 * 10**18
    trade_factory.balance += 10 * 10**18
    fxn_whale.balance += 10 * 10**18

    if which_strategy != 3:
        crv = Contract(strategy.crv(), abi="abis/IERC20.json")
        crv.transfer(strategy, 100 * 10**18, sender=crv_whale)

        # whale can't sweep, but trade handler can
        if not tests_using_tenderly:
            with ape.reverts():
                crv.transferFrom(
                    strategy, whale, int(crv.balanceOf(strategy) / 2), sender=whale
                )

        crv.transferFrom(
            strategy, whale, int(crv.balanceOf(strategy) / 2), sender=trade_factory
        )

        if which_strategy == 2:
            yprisma.transferFrom(
                strategy,
                whale,
                int(yprisma.balanceOf(strategy) / 2),
                sender=trade_factory,
            )

        # remove our trade handler
        strategy.removeTradeFactoryPermissions(True, sender=gov)
        assert strategy.tradeFactory() == ZERO_ADDRESS
        assert crv.balanceOf(strategy) > 0

        # trade factory now cant sweep
        if not tests_using_tenderly:
            with ape.reverts():
                crv.transferFrom(
                    strategy,
                    whale,
                    int(crv.balanceOf(strategy) / 2),
                    sender=trade_factory,
                )
            if which_strategy == 2:
                assert yprisma.allowance(strategy, trade_factory) == 0
                if yprisma.balanceOf(strategy) > 0:
                    with ape.reverts():
                        yprisma.transferFrom(
                            strategy,
                            whale,
                            int(yprisma.balanceOf(strategy) / 2),
                            sender=trade_factory,
                        )

        # give back those permissions, now trade factory can sweep
        strategy.updateTradeFactory(trade_factory, sender=gov)
        crv.transferFrom(
            strategy, whale, int(crv.balanceOf(strategy) / 2), sender=trade_factory
        )
    else:
        fxn = Contract(strategy.fxn(), abi="abis/IERC20.json")
        fxn.transfer(strategy, 100 * 10**18, sender=fxn_whale)

        # whale can't sweep, but trade handler can
        if not tests_using_tenderly:
            with ape.reverts():
                fxn.transferFrom(
                    strategy, whale, int(fxn.balanceOf(strategy) / 2), sender=whale
                )

        fxn.transferFrom(
            strategy, whale, int(fxn.balanceOf(strategy) / 2), sender=trade_factory
        )

        # remove our trade handler
        strategy.removeTradeFactoryPermissions(True, sender=gov)
        assert strategy.tradeFactory() == ZERO_ADDRESS
        assert fxn.balanceOf(strategy) > 0

        # trade factory now cant sweep
        if not tests_using_tenderly:
            with ape.reverts():
                fxn.transferFrom(
                    strategy,
                    whale,
                    int(fxn.balanceOf(strategy) / 2),
                    sender=trade_factory,
                )

        # give back those permissions, now trade factory can sweep
        strategy.updateTradeFactory(trade_factory, sender=gov)
        fxn.transferFrom(
            strategy, whale, int(fxn.balanceOf(strategy) / 2), sender=trade_factory
        )

    # remove again!
    strategy.removeTradeFactoryPermissions(False, sender=gov)

    # update again
    strategy.updateTradeFactory(trade_factory, sender=gov)

    # simulate profits
    increase_time(chain, sleep_time)

    # can't set trade factory to zero
    if not tests_using_tenderly:
        with ape.reverts("revert: Cant remove with this function"):
            strategy.updateTradeFactory(ZERO_ADDRESS, sender=gov)

    # remove again!
    strategy.removeTradeFactoryPermissions(True, sender=gov)

    # update again
    strategy.updateTradeFactory(trade_factory, sender=gov)

    # update our rewards again, shouldn't really change things
    if which_strategy in [0, 4]:  # convex and frax auto-update, prisma has no rewards
        tx = strategy.updateRewards(sender=gov)
        print("Tx ID:", tx)
    elif which_strategy in [1, 3]:  # Curve and FXN input the array
        strategy.updateRewards([], sender=gov)

    # check out our rewardsTokens
    if not tests_using_tenderly:
        if which_strategy == 0:
            # for convex, 0 position may be occupied by wrapped CVX token
            with ape.reverts():
                strategy.rewardsTokens(1)
        if which_strategy in [
            1,
            3,
            4,
        ]:  # Curve and FXN start empty, Frax auto-skips CRV/CVX/FXS
            with ape.reverts():
                strategy.rewardsTokens(0)
        # only vault managers can update rewards, prisma doesn't have extra rewards
        if which_strategy in [1, 3]:
            with ape.reverts():
                strategy.updateRewards([], sender=whale)
        if which_strategy in [0, 4]:
            with ape.reverts():
                strategy.updateRewards(sender=whale)
