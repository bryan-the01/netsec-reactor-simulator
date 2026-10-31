PROGRAM main
  VAR
    Temperature : REAL := 60.0;
    Temperature_x10 : INT AT %MW0 := 600;
    Cooling_ON : BOOL AT %QX0.0 := FALSE;
    High_Temp_Alarm : BOOL AT %QX0.1 := FALSE;
  END_VAR

(*Convert Modbus temperature into Celsius*)
Temperature := INT_TO_REAL(Temperature_x10) / 10.0;

(* Reactor temperature control using hysteresis *)
if Temperature >= 80.0 then
    Cooling_ON := True;
elsif Temperature <= 70.0 then
    Cooling_ON := False;
end_if;

(* High temperature warning *)
High_Temp_Alarm := Temperature >= 90.0;

END_PROGRAM