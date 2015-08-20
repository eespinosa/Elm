# -*- coding: utf-8 -*-
<!--
 *
 *   LinOTP - the open source solution for two factor authentication
 *   Copyright (C) 2010 - 2014 LSE Leading Security Experts GmbH
 *
 *   This file is part of LinOTP server.
 *
 *   This program is free software: you can redistribute it and/or
 *   modify it under the terms of the GNU Affero General Public
 *   License, version 3, as published by the Free Software Foundation.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Affero General Public License for more details.
 *
 *   You should have received a copy of the
 *              GNU Affero General Public License
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *
 *    E-mail: linotp@lsexperts.de
 *    Contact: www.linotp.org
 *    Support: www.lsexperts.de
 *
-->
<h2>${_("Activate Two-Factor Authentication")}</h2>

<div id='elmform'>
    <form class="cmxform" name='myForm'> 
        <fieldset>
            <ol id="provisionElmInstall">
                <li>Install the appropriate authenticator application on your mobile device:
                    <ul>
                        <li>Android, iOS or Blackberry OS 7 and earlier: <a href='http://m.google.com/authenticator' target='extern'>Google Authenticator</a></li>
                        <li>Windows Phone: <a href='http://go.microsoft.com/fwlink/?LinkId=279710' target='extern'>Microsoft Authenticator</a></li>
                        <li>Blackberry OS 10: <a href='http://appworld.blackberry.com/webstore/content/76023/?lang=en' target='extern'>Duo Mobile</a></li>
                    </ul>
                </li>
                <br/>
                <li>Choose a PIN code for the new token. It must have an even number of digits. Your PIN is required whenever you are asked for an access code - for example, if your PIN
                    is 1234 and your one-time-password is 000000, you would enter '1234000000'.
                    <table>
                        <tr><td><span id=error_pin></span></td></tr>
                        <tr>
                            <!--[if lte IE 9]>
                                <td><label class="ie-label" for="elm_pin1">PIN</label></td>
                            <![endif]-->
                            <td><input id="elm_pin1" autocomplete="off" type="password" placeholder="PIN" size="10" tabindex="1" class="text ui-widget-content ui-corner-all"/></td>
                        </tr>
                        <tr>
                            <!--[if lte IE 9]>
                                <td><label class="ie-label" for="elm_pin2">Confirm PIN</label></td>
                            <![endif]-->                        
                            <td><input id="elm_pin2" autocomplete="off" type="password" placeholder="Confirm PIN" size="10" tabindex="1" onkeyup="checkpins('elm_pin1', 'elm_pin2');" class="text ui-widget-content ui-corner-all"/></td>
                        </tr>
                    </table>
                    <button id="showadvanced" class="ui-button ui-button-text-icons ui-button-icon-primary display-button"  onclick="toggleadv(); return false;"></button><br/>
                    <div id="advancedoptions">
                        <p>The default options will work on all software-based TOTP authenticator applications.
                        Some options may not be compatible with the applications listed above. Make sure your application or device
                        supports your selected options before you change anything.</p>
                    <table>
                        <tr>
                            <td><label for="token_type">Token type</label></td>
                            <td><input type="radio" name="token_type" value="elm_totp" id="totp" checked>Time-based HMAC (TOTP)</td>
                            <td><input type="radio" name="token_type" value="elm_hmac" id="hotp">Event-based HMAC (HOTP)</td>
                        </tr>
                        <tr>
                            <td><label for="seed_type">Token seed</label></td>
                            <td><input type="radio" name="seed_type" value="random" id="genseed" checked>Generate random seed</td>
                            <td><input type="radio" name="seed_type" value="manual" id="manualseed">Enter seed
                                <input type="text" id="seedvalue" disabled /></td>
                        </tr>
                        <tr>
                            <td><label for="otplen">OTP digits</label></td>
                            <td><select id="otplen">
                                <option value="6" selected>6</option>
                                <option value="8">8</option>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td><label for="algorithm">Hash algorithm</label></td>
                            <td><select name="algorithm">
                                <option value="sha1" selected>sha1</option>
                                <option value="sha256">sha256</option>
                                <option value="sha512">sha512</option>
                                </select>
                            </td>
                        </tr>
                        <tr id="totp_row">
                            <td><label for="timestep">Time step</label></td>
                                <td><select id="timestep">
                                    <option value='30'>30 seconds</option>
                                    <option value='60'>60 seconds</option>
                                </select></td>
                        </tr>
                    </table></div>
                    <br/>
                    <button class="ui-button ui-button-text-icons ui-button-icon-primary" id="elmprovision" onclick="elmProvision(); return false;"></button>
                </li>
            </ol>
            
            <ol id="provisionElmResultDiv" start="3">
                <li>${_("Token")} ${_("successfully created!")}
                    <p>If you are viewing this site on the same device as your authenticator app, click the following link to activate your code:"
                         <a id=google_link>"Install token"</a>
                    </p>
                    <p>${_("Alternatively, scan the QR code below with your authenticator device.")}</p>
                    <div id="accordion">
                        <h3>QR Code</h3>
                        <div>
                            <span id=google_qr_code></span>
                        </div>
                    </div>
                    <button id="showkey" class="ui-button ui-button-text-icons ui-button-icon-primary display-button"  onclick="togglekey(); return false;"></button>
                    <div id="keyvalues"><table>
                        <tr><td>Secret value: <label id="tokensecret"></label></td></tr>
                        <tr><td>Seed: <label id="tokenkey"></label></td></tr>
                    </table></div>
                </li>
                <br/>
                <li>Enter your PIN followed by a one-time password generated by your authenticator app to complete setup. For example, if your PIN
                    is 1234 and your one-time-password is 000000, you would enter '1234000000'. Note that your authenticator <strong>will not work</strong>
                    on Single Sign On pages until you complete this step.
                    <table>
                        <tr><td><span id=error_otp></span></td></tr>
                        <tr>
                            <!--[if lte IE 9]>
                                <td><label class="ie-label" for="otp">Access Code</label></td>
                            <![endif]-->
                            <td><input id="otp" autocomplete="off" type="password" placeholder="Access Code" size="10" tabindex="1" class="text ui-widget-content ui-corner-all"/></td>
                        </tr>
                    </table>
                    <br/>
                    <button class='action-button' id="elmfinal" onclick="elmProvisionFinal(); return false;">
                        ${_("Finish installation")}
                    </button>
                    <input type=hidden id=token_serial value="">
                </li>
            </ol>
            <div id="provisionElmComplete">
                <p>Your token has now been activated. Single Sign-On pages will now prompt you for an access code when you attempt to login.</p>
            </div>
        </fieldset>
        
    </form>
</div>

<script>
    // Initial display.
    $('#provisionElmInstall').show();
    $('#provisionElmResultDiv').hide();
    $('#provisionElmComplete').hide();
    $('#advancedoptions').hide();
    $('#keyvalues').hide();
    $('#elm_pin2').keypress(function(e){
        if(e.keyCode==13)
        $('#elmprovision').click();
    });
    
    $('#otp').keypress(function(e){
        if(e.keyCode==13)
        $('#elmfinal').click();
    });

    // Set up the accordion drop-down for the QR codes.
    $(function() {
        $("#accordion").accordion({
            'collapsible' : true,
            'active' : false
        });
    });


    // Button icons
    $('#showadvanced' ).button({ icons: { primary: "ui-icon-triangle-1-e" },
                                 label: "Advanced token options" 
                               });
    $('#showkey').button({ icons: { primary: "ui-icon-triangle-1-e" },
                                     label: "Token keys"
                         });
    $('#elmprovision').button({ label: "Activate token" });
    $('#elmfinal').button();

    // Show advanced options
    function toggleadv() {
        if ($('#advancedoptions').css('display') == "none") {
            $('#advancedoptions').show();
            $('#showadvanced').button({ icons: { primary: "ui-icon-triangle-1-s" },
                                     });
        }
        else {
            $('#advancedoptions').hide();
            $('#showadvanced').button({ icons: { primary: "ui-icon-triangle-1-e" },
                                     });
        }
    }

    // Show keys
    function togglekey() {
        if ($('#keyvalues').css('display') == 'none') {
            $('#keyvalues').show();
            $('#showkey').button({ icons: { primary: "ui-icon-triangle-1-s" },
                                });
        }
        else {
            $('#keyvalues').hide();
            $('#showkey').button({ icons: { primary: "ui-icon-triangle-1-e"},
                                });
        }
    }

    // Show manual key entry field
    $('#manualseed').click(function(){ $('#seedvalue').prop("disabled", false); });
    $('#genseed').click(function(){ $('#seedvalue').prop("disabled", true); });

    // Show extra TOTP settings
    $('#totp').click(function(){ $('#totp_row').show(); });
    $('#hotp').click(function(){ $('#totp_row').hide(); });

</script>


