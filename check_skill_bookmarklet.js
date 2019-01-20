javascript:(function(){
    function getStats(levels){ 
        skills = {};
        sections = $(".views-field-field-servant-skill");
    
        tables = sections.find(".stats-skill-table").find("table");
        for(i = 0; i < tables.size(); i++){
            rows = tables.eq(i).find("tr");
            skills[i] = {};
            skills[i].name = sections.find('span > span')[i].innerText;
            skills[i].description = sections.find('p')[i].innerText; 
            skills[i].buffs = {};
            for(j = 1; j < rows.size(); j++){
                buff_name = rows.eq(j).find("th")[0].innerText; 
                buff_buff = rows.eq(j).find("td")[levels[i]].innerText;               
                skills[i].buffs[buff_name] = buff_buff;
            }
        }

        return skills;
    }
    function getSkillNames(){
        skills = {};
        sections = $(".views-field-field-servant-skill");
        for(i = 0; i < sections.size(); i++){
            skills[i] = {};
            skills[i].name = sections.find('span > span')[i].innerText;
        }

        return skills;
    }
    function getSkillSelect(text, name){
    
        value = '<h3>' + text + '</h3>'               +		
        '<select style="color:black;" name="' + name + '">'        +
              '<option value="1">1</option>'  +
              '<option value="2">2</option>'  +
              '<option value="3">3</option>'  +
              '<option value="4">4</option>'  +
              '<option value="5">5</option>'  +
              '<option value="6">6</option>'  +
              '<option value="7">7</option>'  +
              '<option value="8">8</option>'  +
              '<option value="9">9</option>'  +
              '<option value="10">10</option>'+
            '</select>';
        return value;
    }
    function imbedUI(){
        $("body").prepend('<div id="skills_parent" style="text-align: center"><div id="skills_get" style="max-width: 500px; display: inline-block; background: maroon; padding: 5px; border: solid 1px red; text-align: center; color: gold;"></div></div>');
        skills_names = getSkillNames();
        $("#skills_get").append("<h2>Select the current level of each skill</h2>");
        $("#skills_get").append(getSkillSelect(skills_names[0].name, 'skill1'));
        $("#skills_get").append(getSkillSelect(skills_names[1].name, 'skill2'));
        $("#skills_get").append(getSkillSelect(skills_names[2].name, 'skill3'));
        $("#skills_get").append("<input id='skill_info' type='submit' value='Get info' />");
        $("#skills_parent").append("<div id='app_results'></div>");
        $("#skill_info").click(function(){
            console.log("beginning attempt");
            $("#skills_get").css("display", "none");
            $("#app_results").css("display", "inline-block");
            levels = Array(
                $("select[name=skill1]")[0].value - 1,
                $("select[name=skill2]")[0].value - 1,
                $("select[name=skill3]")[0].value - 1
            );
            skills = getStats(levels);

            html = "<div id='app_results' style='padding: 3px; background: rgba(125,0,0,0.1)' >";
            for(i = 0; i < 3; i++){ 
                html += "<h1>" + skills[i].name + " (Level " + (levels[i] + 1) + ")</h1>\n";
                html += "<div>" + skills[i].description + "</div>";
                html += "<table>";
                buffs = skills[i].buffs;
                Object.keys(buffs).forEach(function(key){
                    console.log(key);
                    html += "<tr><th>" + key        + "</th>\n";
                    html += "<td>" + buffs[key] + "</td></tr>\n";
                });
                html += "</table>\n";
            }
            html += "<input id='reset_button' type='Submit' value='Reset' />";
            html +="</div>";
            $("#app_results").replaceWith(html);
            $("#app_results").find("th").css("background", "#f2f2f2");
            $("#app_results").find("td").css("background", "#ffffff");
            $("#app_results").find("th").css("color", "#000000");
            $("#app_results").find("td").css("color", "#000000");
            $("#reset_button").click(function(){
                console.log("trying to reset");
                $("#app_results").css("display", "none");
                $("#skills_get").css("display", "inline-block");
                window.scrollTo(0,0);
            });
            console.log("attempt ended");
        });
    }
    if($("#skills_parent").size() == 0){
        imbedUI();	
        window.scrollTo(0,0);
    }
})();
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	