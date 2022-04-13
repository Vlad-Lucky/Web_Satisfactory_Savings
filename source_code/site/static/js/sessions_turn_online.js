function onchange_game_session_type()
{
    game_session_type = document.getElementById("game_session_type");
    owner_platform = document.getElementById("owner_platform");
    owner_account_name = document.getElementById("owner_account_name");
    if (game_session_type.value == 1)
    {
        owner_platform.removeAttribute("hidden");
        owner_account_name.removeAttribute("hidden");
        owner_platform.style.visibility = "visible";
        owner_account_name.style.visibility = "visible";
    }
    else
    {
        owner_platform.hidden = true;
        owner_account_name.hidden = true;
        owner_platform.style.visibility = "hidden";
        owner_account_name.style.visibility = "hidden";
    }
}
window.onload = onchange_game_session_type;
